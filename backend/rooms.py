"""Room management for video conferencing."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import secrets
from fastapi import WebSocket


@dataclass
class Participant:
    """Represents a participant in a room."""
    user_id: str
    username: str
    websocket: WebSocket


@dataclass
class Room:
    """Represents a meeting room."""
    room_id: str
    participants: Dict[str, Participant] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    @property
    def participant_count(self) -> int:
        return len(self.participants)

    def is_full(self) -> bool:
        return self.participant_count >= 4

    def add_participant(self, participant: Participant) -> bool:
        """Add a participant to the room. Returns False if room is full."""
        if self.is_full():
            return False
        self.participants[participant.user_id] = participant
        self.last_activity = datetime.utcnow()
        return True

    def remove_participant(self, user_id: str) -> bool:
        """Remove a participant from the room."""
        if user_id in self.participants:
            del self.participants[user_id]
            self.last_activity = datetime.utcnow()
            return True
        return False

    def get_participant(self, user_id: str) -> Optional[Participant]:
        return self.participants.get(user_id)

    def get_other_participants(self, user_id: str) -> List[Participant]:
        """Get all participants except the specified user."""
        return [p for uid, p in self.participants.items() if uid != user_id]

    def has_username(self, username: str) -> bool:
        """Check if username is already taken in this room."""
        return any(
            p.username.lower() == username.lower()
            for p in self.participants.values()
        )


class RoomManager:
    """Manages all active rooms."""

    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def create_room(self) -> str:
        """Create a new room with a cryptographically secure ID."""
        # Use secrets for secure random ID (16 bytes = 22 chars URL-safe)
        room_id = secrets.token_urlsafe(12)
        self.rooms[room_id] = Room(room_id=room_id)
        return room_id

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def get_or_create_room(self, room_id: str) -> Room:
        """Get an existing room or create a new one with the given ID."""
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id=room_id)
        return self.rooms[room_id]

    def delete_room(self, room_id: str) -> bool:
        """Delete a room if it exists."""
        if room_id in self.rooms:
            del self.rooms[room_id]
            return True
        return False

    def cleanup_empty_rooms(self):
        """Remove all empty rooms."""
        empty_rooms = [rid for rid, room in self.rooms.items() if room.participant_count == 0]
        for room_id in empty_rooms:
            del self.rooms[room_id]


# Global room manager instance
room_manager = RoomManager()
