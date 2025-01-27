import uuid
from typing import Dict, Optional
from gemini_schema import PlayerState, RoomState
import json
import os
from pathlib import Path
from datetime import datetime

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, RoomState] = {}
        self.save_folder = Path("saves")
        self.save_folder.mkdir(exist_ok=True)
    
    def create_room(self, host_id: str, language: str = 'en') -> str:
        """Create a new room and return its ID"""
        room_id = str(uuid.uuid4())[:8]  # Use first 8 chars for shorter codes
        self.rooms[room_id] = RoomState(
            room_id=room_id,
            host_id=host_id,
            players={},
            language=language
        )
        return room_id
    
    def join_room(self, room_id: str, player_id: str, player_name: str) -> Optional[RoomState]:
        """Add a player to a room"""
        if room_id not in self.rooms:
            return None
            
        room = self.rooms[room_id]
        if player_id not in room.players:
            room.players[player_id] = PlayerState(
                id=player_id,
                name=player_name,
                race="",
                class_name="",
                health_points=0,
                gold=0,
                damage=0,
                level=0,
                magic_1lvl=0,
                magic_2lvl=0
            )
        return room
    
    def leave_room(self, room_id: str, player_id: str) -> bool:
        """Remove a player from a room"""
        if room_id not in self.rooms:
            return False
            
        room = self.rooms[room_id]
        if player_id not in room.players:
            return False
            
        # Remove player from room
        del room.players[player_id]

        # Only change host if leaving player was the host
        if player_id == room.host_id:
            if room.players:
                # Assign new host from remaining players
                room.host_id = next(iter(room.players.keys()))
            else:
                # Delete empty room
                del self.rooms[room_id]
        
        return True
    
    def get_room(self, room_id: str) -> Optional[RoomState]:
        """Get room by ID"""
        return self.rooms.get(room_id)
    
    def update_player(self, room_id: str, player_state: PlayerState) -> bool:
        """Update player state in a room"""
        if room_id not in self.rooms:
            return False
            
        room = self.rooms[room_id]
        if player_state.id in room.players:
            room.players[player_state.id] = player_state
            return True
        return False
    
    def update_room(self, room_state: RoomState) -> bool:
        """Update entire room state"""
        if room_state.room_id not in self.rooms:
            return False
            
        # Preserve language when updating room state
        old_room = self.rooms[room_state.room_id]
        room_state.language = old_room.language
        self.rooms[room_state.room_id] = room_state
        return True
    
    def save_room(self, room_id: str) -> bool:
        """Save room state to file"""
        if room_id not in self.rooms:
            return False
            
        room = self.rooms[room_id]
        save_path = self.save_folder / f"room_{room_id}.json"
        
        try:
            with save_path.open('w') as f:
                json.dump(room.dict(), f, indent=2)
            return True
        except Exception:
            return False
    
    def load_room(self, room_id: str) -> Optional[RoomState]:
        """Load room state from file"""
        save_path = self.save_folder / f"room_{room_id}.json"
        
        if not save_path.exists():
            return None
            
        try:
            with save_path.open('r') as f:
                data = json.load(f)
                room = RoomState(**data)
                self.rooms[room_id] = room
                return room
        except Exception:
            return None
    
    def cleanup_inactive_rooms(self, max_age_minutes: int = 60):
        """Remove rooms that have been inactive for too long"""
        current_time = datetime.now()
        rooms_to_remove = []
        
        for room_id, room in self.rooms.items():
            if room.last_activity:
                age = (current_time - room.last_activity).total_seconds() / 60
                if age > max_age_minutes:
                    rooms_to_remove.append(room_id)
        
        for room_id in rooms_to_remove:
            del self.rooms[room_id] 