from pydantic import BaseModel
from typing import Optional, List, Dict, Union
from datetime import datetime

class RoomMessage(BaseModel):
    user_message: str
    dm_response: str
    player_name: Optional[str] = None
    timestamp: datetime = datetime.now()

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
    message_history: List[RoomMessage] = []
    has_started: bool = False

class PlayerUpdate(BaseModel):
    player_id: str
    health_points: Optional[int] = None
    gold: Optional[int] = None
    damage: Optional[int] = None
    level: Optional[int] = None
    magic_1lvl: Optional[int] = None
    magic_2lvl: Optional[int] = None
    in_combat: Optional[bool] = None
    dice_roll_needed: Optional[bool] = None
    dice_type: Optional[str] = None

class CombatResult(BaseModel):
    damage_dealt: Optional[int] = None
    damage_taken: Optional[int] = None
    outcome: Optional[str] = None

class DiceRoll(BaseModel):
    required: bool
    type: Optional[str] = None
    reason: Optional[str] = None

# Define the schema as a dictionary that matches Gemini's expected format
GAME_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "message": {
            "type": "STRING",
            "description": "The message from the DM to all players"
        },
        "players_update": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "player_id": {"type": "STRING"},
                    "health_points": {"type": "INTEGER"},
                    "gold": {"type": "INTEGER"},
                    "damage": {"type": "INTEGER"},
                    "level": {"type": "INTEGER"},
                    "magic_1lvl": {"type": "INTEGER"},
                    "magic_2lvl": {"type": "INTEGER"},
                    "in_combat": {"type": "BOOLEAN"},
                    "dice_roll_needed": {"type": "BOOLEAN"},
                    "dice_type": {"type": "STRING"}
                },
                "required": ["player_id"]
            },
            "description": "Updates for specific players' states"
        },
        "combat_result": {
            "type": "OBJECT",
            "properties": {
                "damage_dealt": {"type": "INTEGER"},
                "damage_taken": {"type": "INTEGER"},
                "outcome": {"type": "STRING"}
            },
            "description": "Results of combat actions"
        },
        "dice_roll": {
            "type": "OBJECT",
            "properties": {
                "required": {"type": "BOOLEAN"},
                "type": {"type": "STRING"},
                "reason": {"type": "STRING"}
            },
            "description": "Information about required dice rolls"
        }
    },
    "required": ["message"]
} 