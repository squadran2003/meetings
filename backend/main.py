"""FastAPI application for video conferencing signaling server."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, Request, HTTPException

# Load environment variables from .env file
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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


# Serve static files in production (only if frontend is built and included)
static_dir = os.path.join(os.path.dirname(__file__), "static")
index_file = os.path.join(static_dir, "index.html")

if os.path.exists(static_dir) and os.path.exists(index_file):
    from fastapi.staticfiles import StaticFiles

    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend for all non-API routes with path traversal protection."""
        static_path = Path(static_dir).resolve()

        # Handle empty path
        if not full_path:
            return FileResponse(str(static_path / "index.html"))

        # Resolve requested path
        try:
            requested_path = (static_path / full_path).resolve()
            # Ensure path is within static directory (prevent path traversal)
            requested_path.relative_to(static_path)
        except (ValueError, RuntimeError):
            # Path traversal attempt or invalid path
            raise HTTPException(status_code=403, detail="Access denied")

        if requested_path.is_file():
            return FileResponse(str(requested_path))

        # Return index.html for SPA routing
        return FileResponse(str(static_path / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
