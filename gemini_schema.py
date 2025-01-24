from pydantic import BaseModel
from typing import Optional, List, Dict, Union
from datetime import datetime

class PlayerState(BaseModel):
    id: str
    name: str
    race: str
    class_name: str
    health_points: int
    gold: int
    damage: int
    level: int
    magic_1lvl: int
    magic_2lvl: int
    last_dice_roll: Optional[int] = None
    dice_roll_needed: bool = False
    dice_type: Optional[str] = None
    is_active: bool = True
    last_activity: Optional[datetime] = None

class RoomState(BaseModel):
    room_id: str
    host_id: str
    players: Dict[str, PlayerState]
    language: str = 'en'
    in_combat: bool = False
    enemy_health: Optional[int] = None
    enemy_name: Optional[str] = None
    last_activity: Optional[datetime] = None
    created_at: datetime = datetime.now()

# Define the schema as a dictionary that matches Gemini's expected format
GAME_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "message": {
            "type": "STRING",
            "description": "The message from the DM to all players"
        },
        "state_update": {
            "type": "OBJECT",
            "properties": {
                "health_points": {"type": "INTEGER"},
                "gold": {"type": "INTEGER"},
                "damage": {"type": "INTEGER"},
                "level": {"type": "INTEGER"},
                "magic_1lvl": {"type": "INTEGER"},
                "magic_2lvl": {"type": "INTEGER"},
                "dice_roll_needed": {"type": "BOOLEAN"},
                "dice_type": {"type": "STRING"},
                "enemy_health": {"type": "INTEGER"},
                "in_combat": {"type": "BOOLEAN"}
            },
            "description": "Updates for the game state"
        }
    }
} 