"""FastAPI application for video conferencing signaling server."""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Request, HTTPException

# Load environment variables from .env file
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from signaling import handle_websocket
from rooms import room_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Allowed origins for CORS and WebSocket
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

# Add production origins from environment
PRODUCTION_ORIGIN = os.getenv("ALLOWED_ORIGIN")
if PRODUCTION_ORIGIN:
    ALLOWED_ORIGINS.append(PRODUCTION_ORIGIN)

app = FastAPI(title="Meetings API")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):  # noqa
    _ = request, exc  # Required by FastAPI exception handler signature
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded. Please try again later."}
    )


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "media-src 'self' blob:; "
            "connect-src 'self' wss: ws:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Permissions for camera/microphone
        response.headers["Permissions-Policy"] = (
            "camera=*, microphone=*, display-capture=*"
        )

        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS configuration - restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# TURN credential cache (fetched from Metered.ca API)
_turn_cache: dict = {"iceServers": None, "expires": 0}
METERED_API_KEY = os.getenv("METERED_API_KEY", "")


@app.get("/api/turn-credentials")
@limiter.limit("10/minute")
async def get_turn_credentials(request: Request):  # noqa: ARG001
    """Return ICE servers including TURN credentials.

    Fetches from Metered.ca API and caches for 12 hours.
    If no API key is configured, returns STUN-only servers.
    """
    _ = request
    import time

    stun_only = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
        ]
    }

    if not METERED_API_KEY:
        return stun_only

    now = time.time()
    if _turn_cache["iceServers"] and now < _turn_cache["expires"]:
        return {"iceServers": _turn_cache["iceServers"]}

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"https://meetings.metered.live/api/v1/turn/credentials"
                f"?apiKey={METERED_API_KEY}"
            )
            resp.raise_for_status()
            servers = resp.json()
            _turn_cache["iceServers"] = servers
            _turn_cache["expires"] = now + 43200  # 12 hours
            return {"iceServers": servers}
    except Exception as e:
        logger.warning(f"Failed to fetch TURN credentials: {e}")
        if _turn_cache["iceServers"]:
            return {"iceServers": _turn_cache["iceServers"]}
        return stun_only


@app.post("/api/rooms")
@limiter.limit("10/minute")
async def create_room(request: Request):  # noqa: ARG001
    """Create a new meeting room."""
    _ = request  # Required for rate limiting
    room_id = room_manager.create_room()
    return {"roomId": room_id}


@app.get("/api/rooms/{room_id}")
@limiter.limit("30/minute")
async def get_room(request: Request, room_id: str):  # noqa: ARG001
    """Get room information."""
    _ = request  # Required for rate limiting
    # Validate room_id format (alphanumeric and URL-safe chars only)
    if not room_id or len(room_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid room ID")

    room = room_manager.get_room(room_id)
    if not room:
        # Don't reveal whether room exists or not for security
        return {"exists": False, "participantCount": 0, "isFull": False}

    return {
        "exists": True,
        "roomId": room_id,
        "participantCount": room.participant_count,
        "isFull": room.is_full()
    }


@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    """WebSocket endpoint for signaling."""
    # Validate origin
    origin = websocket.headers.get("origin", "")
    if origin:
        # Auto-allow same-origin connections (frontend served by this backend)
        from urllib.parse import urlparse
        origin_host = urlparse(origin).netloc
        request_host = websocket.headers.get("host", "")
        is_same_origin = origin_host == request_host

        if not is_same_origin and origin not in ALLOWED_ORIGINS:
            logger.warning(f"Rejected WebSocket from invalid origin: {origin}")
            await websocket.close(code=1008, reason="Invalid origin")
            return

    # Validate room_id and user_id
    if not room_id or len(room_id) > 50:
        await websocket.close(code=1008, reason="Invalid room ID")
        return

    if not user_id or len(user_id) > 50:
        await websocket.close(code=1008, reason="Invalid user ID")
        return

    await handle_websocket(websocket, room_id, user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
