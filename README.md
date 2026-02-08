# Video Conferencing App

A Zoom-like video conferencing application supporting 2-4 participants with video/audio calls and text chat.

## Features

- Video and audio calls with up to 4 participants
- Peer-to-peer WebRTC connections (mesh topology)
- Real-time text chat
- Screen sharing
- Mute/unmute audio and video controls
- Copy meeting link to share

## Tech Stack

- **Backend**: FastAPI + WebSockets (Python)
- **Frontend**: Vue 3 + Vite + Pinia
- **WebRTC**: simple-peer library
- **Signaling**: WebSocket-based

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activatedghdhgds
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

### Docker (Alternative)

```bash
docker compose up
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Production Deployment

### Build Frontend

```bash
cd frontend
npm run build
```

### Deploy with Docker

```bash
# Copy frontend build to backend static folder
cp -r frontend/dist backend/static

# Run production container
docker compose -f docker-compose.prod.yml up -d
```

### AWS Lightsail

See `deploy/lightsail-setup.sh` for full setup instructions.

## ICE Servers

The app uses Google's free STUN servers. For production, add TURN servers for better connectivity behind restrictive NATs.

Get free TURN credentials from [Metered.ca](https://www.metered.ca/tools/openrelay/) and update `frontend/src/composables/useWebRTC.js`.

## Testing

1. Start backend and frontend
2. Open two browser tabs
3. Create a meeting in one tab
4. Copy the meeting code and join from the other tab
5. Allow camera/microphone permissions
6. Video and audio should work between tabs

For multi-device testing, use ngrok or deploy to a server with HTTPS.
