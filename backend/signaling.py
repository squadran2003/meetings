"""WebSocket signaling server for WebRTC negotiation."""

import logging
import re
from collections import defaultdict
from html import escape
from time import time
from typing import Any, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
import bleach

from rooms import room_manager, Participant

logger = logging.getLogger(__name__)

# Valid message types and their required state
VALID_MESSAGE_TYPES = {
    "join": {"requires_joined": False},
    "offer": {"requires_joined": True},
    "answer": {"requires_joined": True},
    "ice-candidate": {"requires_joined": True},
    "chat": {"requires_joined": True},
    "leave": {"requires_joined": False},
}

# Rate limiting: track message timestamps per user
message_timestamps: dict = defaultdict(list)
RATE_LIMIT_MESSAGES = 30  # messages
RATE_LIMIT_WINDOW = 10  # seconds


def check_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded rate limit. Returns True if allowed."""
    now = time()
    # Clean old timestamps
    message_timestamps[user_id] = [
        t for t in message_timestamps[user_id]
        if now - t < RATE_LIMIT_WINDOW
    ]

    if len(message_timestamps[user_id]) >= RATE_LIMIT_MESSAGES:
        return False

    message_timestamps[user_id].append(now)
    return True


def validate_username(username: str) -> Optional[str]:
    """Validate and sanitize username. Returns sanitized name or None if invalid."""
    if not username or not isinstance(username, str):
        return None

    # Strip whitespace
    username = username.strip()

    # Length check
    if len(username) < 1 or len(username) > 50:
        return None

    # Remove any HTML
    username = bleach.clean(username, tags=[], strip=True)

    # Collapse multiple spaces
    username = re.sub(r'\s+', ' ', username)

    # Final length check after sanitization
    if len(username) < 1:
        return None

    return username[:50]


def validate_chat_message(message: str) -> Optional[str]:
    """Validate and sanitize chat message. Returns sanitized message or None."""
    if not message or not isinstance(message, str):
        return None

    # Length check
    if len(message) > 1000:
        return None

    # Strip and sanitize
    message = message.strip()
    if not message:
        return None

    # Remove HTML tags
    message = bleach.clean(message, tags=[], strip=True)

    # Escape HTML entities for safe display
    message = escape(message)

    return message[:1000]


def validate_user_id(user_id: str) -> bool:
    """Validate user ID format."""
    if not user_id or not isinstance(user_id, str):
        return False
    # Allow alphanumeric, hyphens, underscores (URL-safe base64 chars)
    return bool(re.match(r'^[a-zA-Z0-9_-]{1,50}$', user_id))


async def send_message(websocket: WebSocket, message: dict):
    """Send a JSON message to a WebSocket."""
    try:
        await websocket.send_json(message)
    except Exception:
        pass


async def send_error(websocket: WebSocket, error_msg: str):
    """Send an error message to the client."""
    await send_message(websocket, {"type": "error", "message": error_msg})


async def broadcast_to_room(room_id: str, message: dict, exclude_user: str = None):
    """Broadcast a message to all participants in a room except the excluded user."""
    room = room_manager.get_room(room_id)
    if not room:
        return

    for user_id, participant in room.participants.items():
        if user_id != exclude_user:
            await send_message(participant.websocket, message)


async def send_to_user(room_id: str, target_user_id: str, message: dict):
    """Send a message to a specific user in a room."""
    room = room_manager.get_room(room_id)
    if not room:
        return

    participant = room.get_participant(target_user_id)
    if participant:
        await send_message(participant.websocket, message)


async def handle_join(room_id: str, user_id: str, username: str, websocket: WebSocket) -> bool:
    """Handle a user joining a room."""
    # Validate username
    clean_username = validate_username(username)
    if not clean_username:
        await send_error(websocket, "Invalid username")
        return False

    room = room_manager.get_or_create_room(room_id)

    # Check if room is full
    if room.is_full():
        await send_error(websocket, "Room is full (maximum 4 participants)")
        return False

    # Check for duplicate username
    if room.has_username(clean_username):
        await send_error(websocket, "Username already taken in this room")
        return False

    # Create participant
    participant = Participant(user_id=user_id, username=clean_username, websocket=websocket)

    # Get existing participants before adding new one
    existing_participants = [
        {"userId": p.user_id, "username": p.username}
        for p in room.get_other_participants(user_id)
    ]

    # Add to room
    room.add_participant(participant)

    # Send room info to the joining user
    await send_message(websocket, {
        "type": "room-info",
        "roomId": room_id,
        "participants": existing_participants
    })

    # Notify other participants
    await broadcast_to_room(room_id, {
        "type": "user-joined",
        "userId": user_id,
        "username": clean_username
    }, exclude_user=user_id)

    return True


async def handle_leave(room_id: str, user_id: str):
    """Handle a user leaving a room."""
    room = room_manager.get_room(room_id)
    if not room:
        return

    participant = room.get_participant(user_id)
    username = participant.username if participant else "Unknown"

    room.remove_participant(user_id)

    # Notify other participants
    await broadcast_to_room(room_id, {
        "type": "user-left",
        "userId": user_id,
        "username": username
    })

    # Cleanup empty room
    if room.participant_count == 0:
        room_manager.delete_room(room_id)

    # Cleanup rate limit data
    if user_id in message_timestamps:
        del message_timestamps[user_id]


async def handle_offer(room_id: str, from_user: str, to_user: str, offer: Any):
    """Forward WebRTC offer to target user."""
    if not validate_user_id(to_user):
        return

    await send_to_user(room_id, to_user, {
        "type": "offer",
        "fromUserId": from_user,
        "offer": offer
    })


async def handle_answer(room_id: str, from_user: str, to_user: str, answer: Any):
    """Forward WebRTC answer to target user."""
    if not validate_user_id(to_user):
        return

    await send_to_user(room_id, to_user, {
        "type": "answer",
        "fromUserId": from_user,
        "answer": answer
    })


async def handle_ice_candidate(room_id: str, from_user: str, to_user: str, candidate: Any):
    """Forward ICE candidate to target user."""
    if not validate_user_id(to_user):
        return

    await send_to_user(room_id, to_user, {
        "type": "ice-candidate",
        "fromUserId": from_user,
        "candidate": candidate
    })


async def handle_chat(room_id: str, from_user: str, username: str, message: str):
    """Broadcast chat message to all participants in the room."""
    # Validate and sanitize message
    clean_message = validate_chat_message(message)
    if not clean_message:
        return

    await broadcast_to_room(room_id, {
        "type": "chat",
        "fromUserId": from_user,
        "username": username,
        "message": clean_message
    })


async def handle_websocket(websocket: WebSocket, room_id: str, user_id: str):
    """Main WebSocket handler for signaling."""
    await websocket.accept()

    joined = False
    username = f"User-{user_id[:4]}"

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # Validate message type
            if msg_type not in VALID_MESSAGE_TYPES:
                await send_error(websocket, "Invalid message type")
                continue

            # Check if message requires user to be joined
            if VALID_MESSAGE_TYPES[msg_type]["requires_joined"] and not joined:
                await send_error(websocket, "Must join room first")
                continue

            # Rate limiting
            if not check_rate_limit(user_id):
                await send_error(websocket, "Rate limit exceeded. Please slow down.")
                continue

            if msg_type == "join":
                if joined:
                    await send_error(websocket, "Already joined")
                    continue
                raw_username = data.get("username", username)
                joined = await handle_join(room_id, user_id, raw_username, websocket)
                if joined:
                    # Update username to the validated one
                    room = room_manager.get_room(room_id)
                    if room:
                        participant = room.get_participant(user_id)
                        if participant:
                            username = participant.username
                else:
                    break

            elif msg_type == "offer":
                to_user = data.get("toUserId")
                offer = data.get("offer")
                if to_user and offer:
                    await handle_offer(room_id, user_id, to_user, offer)

            elif msg_type == "answer":
                to_user = data.get("toUserId")
                answer = data.get("answer")
                if to_user and answer:
                    await handle_answer(room_id, user_id, to_user, answer)

            elif msg_type == "ice-candidate":
                to_user = data.get("toUserId")
                candidate = data.get("candidate")
                if to_user and candidate:
                    await handle_ice_candidate(room_id, user_id, to_user, candidate)

            elif msg_type == "chat":
                await handle_chat(
                    room_id,
                    user_id,
                    username,
                    data.get("message", "")
                )

            elif msg_type == "leave":
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user_id[:8]}, room={room_id[:8]}")
    except Exception as e:
        logger.error(f"WebSocket error: user={user_id[:8]}, error={type(e).__name__}")
    finally:
        if joined:
            await handle_leave(room_id, user_id)
