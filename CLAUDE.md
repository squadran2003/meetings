# Meetings - Video Conferencing App

A Zoom-like peer-to-peer video conferencing application supporting 2-4 participants with video/audio calls, text chat, and screen sharing.

## Architecture Overview

```
meetings/
├── backend/          # Python FastAPI signaling server
│   ├── main.py       # FastAPI app, routes, middleware, static serving
│   ├── signaling.py  # WebSocket message handling & WebRTC signaling
│   ├── rooms.py      # Room & participant data models
│   ├── requirements.txt
│   ├── runtime.txt   # Python 3.11.7
│   └── Dockerfile
├── frontend/         # Vue 3 SPA
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.js           # App entry, router setup
│       ├── App.vue           # Root component (just router-view)
│       ├── config.js         # Env-based config (API_URL, WS_URL, ICE_SERVERS)
│       ├── views/
│       │   ├── Home.vue      # Landing page: create/join meeting
│       │   └── Meeting.vue   # Meeting room: orchestrates media, signaling, WebRTC
│       ├── components/
│       │   ├── VideoGrid.vue       # Responsive grid layout for video tiles
│       │   ├── ParticipantVideo.vue # Single video tile with avatar fallback
│       │   ├── Controls.vue        # Bottom bar: mute, camera, screen share, chat, leave
│       │   └── Chat.vue            # Slide-out chat panel
│       ├── composables/
│       │   ├── useMediaStream.js   # Camera/mic/screen capture via getUserMedia
│       │   ├── useSignaling.js     # WebSocket client for signaling server
│       │   └── useWebRTC.js        # Peer connections via simple-peer (mesh topology)
│       └── stores/
│           └── meeting.js          # Pinia store: room state, participants, streams
├── deploy/
│   └── start.sh      # AWS Lightsail setup script (Ubuntu + Docker + nginx + certbot)
├── docker-compose.yml      # Dev: separate frontend (port 3000) + backend (port 8000)
├── docker-compose.prod.yml # Prod: single container, frontend built into backend/static
├── nixpacks.toml           # Railway deployment config
├── Procfile                # Railway/Heroku process definition
└── railway.json            # Railway deployment settings
```

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.11, FastAPI, Uvicorn       |
| WebSocket  | FastAPI WebSockets + websockets lib |
| Frontend   | Vue 3 (Composition API), Vite 5     |
| State      | Pinia                               |
| Routing    | vue-router 4                        |
| WebRTC     | simple-peer (mesh P2P)              |
| Sanitizing | bleach (backend), manual (frontend) |
| Rate limit | slowapi (backend)                   |

## How It Works

### Connection Flow

1. **Home page** (`Home.vue`): User enters name, creates or joins a room
2. **Room creation**: `POST /api/rooms` generates a cryptographically secure room ID (`secrets.token_urlsafe`)
3. **Meeting page** (`Meeting.vue`): Initializes camera/mic, connects WebSocket, joins room
4. **WebSocket signaling** (`/ws/{room_id}/{user_id}`): Handles join/leave/offer/answer/ICE/chat messages
5. **WebRTC mesh**: Each participant connects to every other participant directly via simple-peer
6. **New participant joins**: Gets `room-info` with existing participants list, then initiates peer connections as initiator

### WebSocket Message Types

| Type           | Direction      | Purpose                          |
|----------------|----------------|----------------------------------|
| `join`         | Client -> Server | Join room with username         |
| `room-info`    | Server -> Client | List of existing participants   |
| `user-joined`  | Server -> Others | Notify new participant          |
| `user-left`    | Server -> Others | Notify departure                |
| `offer`        | Client -> Client | WebRTC SDP offer (via server)   |
| `answer`       | Client -> Client | WebRTC SDP answer (via server)  |
| `ice-candidate`| Client -> Client | ICE candidate (via server)      |
| `chat`         | Client -> All    | Chat message broadcast          |
| `error`        | Server -> Client | Error notification              |

### Key Constraints

- **Max 4 participants per room** (enforced in `rooms.py:Room.is_full()`)
- **Mesh topology**: Every participant connects to every other (P2P), no SFU/MCU
- **In-memory rooms**: No database, rooms exist only while participants are connected
- **STUN only by default**: Uses Google STUN servers; TURN can be added via env vars
- **Username uniqueness**: Enforced per-room (case-insensitive)

## Development

### Local Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev    # runs on port 3000, proxies /api and /ws to :8000
```

### Docker

```bash
docker compose up   # frontend :3000, backend :8000
```

### Frontend Environment Variables

| Variable              | Purpose                        | Default                |
|-----------------------|--------------------------------|------------------------|
| `VITE_API_URL`        | Backend API base URL           | `""` (same origin)    |
| `VITE_WS_URL`        | WebSocket base URL             | `""` (auto-detect)    |
| `VITE_BACKEND_DEV_URL`| Vite proxy target for dev     | `http://localhost:8000`|
| `VITE_TURN_URL`      | TURN server URL                | (none)                 |
| `VITE_TURN_USERNAME`  | TURN server username           | (none)                 |
| `VITE_TURN_CREDENTIAL`| TURN server credential        | (none)                 |

### Backend Environment Variables

| Variable          | Purpose                       | Default         |
|-------------------|-------------------------------|-----------------|
| `ENVIRONMENT`     | `development` or `production` | `development`   |
| `ALLOWED_ORIGIN`  | Extra CORS origin for prod    | (none)          |

## Production Deployment

Frontend is built (`npm run build`) and copied to `backend/static/`. The FastAPI backend serves both the API and the SPA (with path traversal protection). Deployed on **Railway** via nixpacks.

### Static File Serving (Production)

`main.py` checks if `backend/static/index.html` exists at startup. If so, it mounts `/assets` and serves `index.html` as a catch-all for SPA routing.

## Security Features

- **CORS**: Restricted origins (configured in `main.py:ALLOWED_ORIGINS`)
- **WebSocket origin validation**: Checks origin header, allows same-origin or allowlisted
- **Security headers**: X-Content-Type-Options, X-Frame-Options, CSP, Permissions-Policy
- **Input sanitization**: bleach + html.escape on backend; regex strip on frontend
- **Rate limiting**: slowapi on HTTP endpoints, custom per-user rate limit on WebSocket messages (30 msg / 10 sec)
- **Path traversal protection**: `Path.resolve()` + `relative_to()` check on static file serving
- **Secure IDs**: `secrets.token_urlsafe` for room IDs, `crypto.getRandomValues` for user IDs

## Common Tasks

### Adding a new WebSocket message type

1. Add to `VALID_MESSAGE_TYPES` dict in `backend/signaling.py`
2. Add handler function in `backend/signaling.py`
3. Add case in the `handle_websocket` message loop
4. Add `signaling.on(type, handler)` in `frontend/src/composables/useWebRTC.js:setupSignalingHandlers()`
5. Add send function in `frontend/src/composables/useSignaling.js`

### Adding a new UI control

1. Add button in `frontend/src/components/Controls.vue`
2. Emit event up to `Meeting.vue`
3. Add state to `frontend/src/stores/meeting.js` if needed
4. Wire up in `Meeting.vue` event handlers

### Adding persistent storage

Currently all state is in-memory. To persist rooms/messages, you would need to:
1. Add a database (e.g., SQLite, PostgreSQL)
2. Modify `RoomManager` in `backend/rooms.py` to use DB
3. Add migrations/models

## Known Limitations

- No authentication or user accounts
- No reconnection handling (if WebSocket drops, user must rejoin)
- No recording capability
- Screen sharing replaces camera stream (doesn't add a second stream)
- Chat messages are not persisted (lost when all participants leave)
- No TURN server by default (calls may fail behind strict NATs/firewalls)
- Video grid supports max 4 tiles (2x2 layout)
