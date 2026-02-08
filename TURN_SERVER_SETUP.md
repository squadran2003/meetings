# TURN Server Setup Plan

## Why You Need a TURN Server

WebRTC tries to connect users directly (peer-to-peer). When both users are behind routers/NAT, direct connection often fails. A TURN server relays the video/audio traffic as a fallback.

```
Without TURN (fails ~20% of the time):
  Phone ──> [NAT] ──X──> [NAT] <── Laptop

With TURN (always works):
  Phone ──> [NAT] ──> TURN Server <── [NAT] <── Laptop
```

## Option A: Self-Hosted Coturn on a VPS (Recommended)

Coturn is the standard open-source TURN server. A $5-10/month VPS is enough for 2-4 participants.

### Requirements

- Linux VPS with a **public IP address** (DigitalOcean, Vultr, Linode, AWS Lightsail)
- Minimum specs: 1 vCPU, 1GB RAM, 20GB disk
- Open ports: **3478** (UDP+TCP), **5349** (TLS), **49152-65535** (UDP relay range)
- A domain name (optional but recommended for TLS)

### Step 1: Provision a VPS

Any cheap VPS works. Estimated costs:

| Provider        | Plan            | Cost      |
|-----------------|-----------------|-----------|
| DigitalOcean    | Basic Droplet   | $6/month  |
| Vultr           | Cloud Compute   | $5/month  |
| Linode          | Nanode 1GB      | $5/month  |
| AWS Lightsail   | 1GB instance    | $5/month  |

### Step 2: Install Coturn

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y coturn

# Enable coturn as a service
sudo sed -i 's/#TURNSERVER_ENABLED=1/TURNSERVER_ENABLED=1/' /etc/default/coturn
```

### Step 3: Configure Coturn

Create/edit `/etc/turnserver.conf`:

```ini
# Network
listening-port=3478
tls-listening-port=5349
external-ip=YOUR_SERVER_PUBLIC_IP
relay-ip=YOUR_SERVER_PUBLIC_IP

# Relay port range
min-port=49152
max-port=65535

# Domain
realm=turn.yourdomain.com
server-name=turn.yourdomain.com

# Authentication (use time-limited credentials via shared secret)
use-auth-secret
static-auth-secret=GENERATE_A_LONG_RANDOM_SECRET_HERE

# TLS (optional but recommended)
# cert=/etc/letsencrypt/live/turn.yourdomain.com/fullchain.pem
# pkey=/etc/letsencrypt/live/turn.yourdomain.com/privkey.pem

# Security
no-multicast-peers
no-cli
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.168.0.0-192.168.255.255

# Logging
log-file=/var/log/turnserver.log
verbose
```

Generate a random secret:
```bash
openssl rand -hex 32
```

### Step 4: Open Firewall Ports

```bash
sudo ufw allow 3478/tcp
sudo ufw allow 3478/udp
sudo ufw allow 5349/tcp
sudo ufw allow 5349/udp
sudo ufw allow 49152:65535/udp
```

### Step 5: Start Coturn

```bash
sudo systemctl restart coturn
sudo systemctl enable coturn
```

### Step 6: Integrate with Your Backend

The backend generates time-limited credentials using the shared secret. The credential format is:

- **Username**: `{expiry_timestamp}:{any_username}`
- **Password**: `Base64(HMAC-SHA1(username, shared_secret))`

Add this to `backend/main.py`:

```python
import hmac, hashlib, base64, time

TURN_SECRET = os.getenv("TURN_SECRET")
TURN_HOST = os.getenv("TURN_HOST")  # e.g. "turn.yourdomain.com"

@app.get("/api/turn-credentials")
async def get_turn_credentials():
    if not TURN_SECRET or not TURN_HOST:
        return {"iceServers": [{"urls": "stun:stun.l.google.com:19302"}]}

    expiry = int(time.time()) + 86400  # 24 hours
    username = f"{expiry}:meetings"
    password = base64.b64encode(
        hmac.new(TURN_SECRET.encode(), username.encode(), hashlib.sha1).digest()
    ).decode()

    return {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {
                "urls": [
                    f"turn:{TURN_HOST}:3478?transport=udp",
                    f"turn:{TURN_HOST}:3478?transport=tcp",
                    f"turns:{TURN_HOST}:5349?transport=tcp",
                ],
                "username": username,
                "credential": password,
            },
        ]
    }
```

### Step 7: Set Environment Variables (Railway)

```
TURN_SECRET=your_generated_secret_from_step_3
TURN_HOST=turn.yourdomain.com
```

### Step 8: Test

1. Open https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/
2. Enter your TURN server URL: `turn:YOUR_IP:3478`
3. Enter a generated username/password from your API
4. Click "Gather candidates"
5. You should see candidates with type **relay** -- that means TURN is working

---

## Option B: Coturn via Docker (on any server)

If you prefer Docker over installing packages directly:

```yaml
# docker-compose.turn.yml
version: '3.8'
services:
  coturn:
    image: coturn/coturn:latest
    network_mode: host
    volumes:
      - ./turnserver.conf:/etc/turnserver.conf:ro
    restart: unless-stopped
```

Use the same `turnserver.conf` from Option A. Run with:
```bash
docker compose -f docker-compose.turn.yml up -d
```

**Note**: `network_mode: host` is important for TURN -- it needs direct access to the full UDP port range.

---

## Option C: Coturn on Railway (Same Platform)

Railway supports Docker images. This keeps everything on one platform but has limitations.

### Steps:
1. In Railway dashboard, add a new service
2. Select "Docker Image" and enter `coturn/coturn`
3. Set environment variables for coturn configuration
4. Expose ports 3478 and 5349

### Limitations:
- Railway's UDP support may be limited
- The large relay port range (49152-65535) may not map correctly
- Bandwidth-based pricing could get expensive for video relay
- **Not recommended** for production TURN -- a dedicated VPS is better

---

## Option D: Managed TURN Service (Zero Ops)

If you don't want to manage a server at all:

| Service      | Free Tier      | Paid           | Notes                          |
|--------------|----------------|----------------|--------------------------------|
| Metered.ca   | 20 GB/month    | $99/month      | Easiest setup, REST API        |
| Twilio       | Limited free   | Pay-per-use    | Well documented                |
| Xirsys       | 500 MB/month   | $49/month      | Simple dashboard               |

For metered.ca:
1. Sign up at https://dashboard.metered.ca/signup
2. Create an app, get your API key
3. Set `METERED_API_KEY=your_key` in Railway env vars
4. The backend already has `/api/turn-credentials` endpoint for this

---

## Recommended Path

For your project (small scale, 2-4 participants):

1. **Start with**: Metered.ca free tier (20GB/month, zero setup)
2. **When outgrowing free tier**: Self-host coturn on a $5/month VPS (Option A)
3. **Don't bother with**: Railway-hosted coturn (Option C) -- too many limitations

### Bandwidth Estimates

| Scenario                     | TURN Bandwidth/hour | Monthly (1hr/day) |
|------------------------------|--------------------|--------------------|
| 2 participants, 720p video   | ~1.8 GB           | ~54 GB             |
| 4 participants, 720p video   | ~7.2 GB           | ~216 GB            |
| 2 participants, audio only   | ~0.1 GB           | ~3 GB              |

Note: TURN is only used when direct P2P fails (~20% of connections). Actual TURN bandwidth is typically much lower than these maximums.

---

## Integration Summary

Regardless of which option you choose, the frontend/backend integration is the same:

1. Frontend calls `GET /api/turn-credentials` on meeting join
2. Backend returns ICE servers array (STUN + TURN with credentials)
3. Frontend passes ICE servers to `new SimplePeer({ config: { iceServers } })`
4. WebRTC uses STUN first, falls back to TURN if needed

This is already implemented in the codebase. You just need to set the right env vars for whichever TURN provider/server you choose.
