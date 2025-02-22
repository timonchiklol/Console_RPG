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
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    last_dice_detail: Optional[dict] = None

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
    player_race: Optional[str] = None
    player_class: Optional[str] = None
    health_points: Optional[int] = None
    gold: Optional[int] = None
    damage: Optional[int] = None
    level: Optional[int] = None
    magic_1lvl: Optional[int] = None
    magic_2lvl: Optional[int] = None
    in_combat: Optional[bool] = None
    dice_roll_needed: Optional[bool] = None
    dice_type: Optional[str] = None
    ability_modifier: Optional[str] = None
    proficient: Optional[bool] = None
    ability_scores: Optional[Dict[str, int]] = None

class CombatResult(BaseModel):
    damage_dealt: Optional[int] = None
    damage_taken: Optional[int] = None
    outcome: Optional[str] = None

class DiceRoll(BaseModel):
    required: bool
    type: Optional[str] = None
    reason: Optional[str] = None
    modifier: Optional[Dict[str, Union[str, bool]]] = None

# Define the schema as a dictionary that matches Gemini's expected format
GAME_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
            "description": "The DM message to all players."
        },
        "player_update_required": {
            "type": "boolean",
            "description": "Boolean flag indicating if a player updates are required."
        },
        "dice_roll_required": {
            "type": "boolean",
            "description": "Boolean flag indicating if a dice roll is required."
        },
        "combat_started": {
            "type": "boolean",
            "description": "Boolean flag indicating if combat has started."
        },
        "players_update": {
            "type": "array",
            "description": "Array of player updates, only present if player_update_required is true.",
            "items": {
                "type": "object",
                "properties": {
                    "player_id": { "type": "string" },
                    "health_points": { "type": "integer" },
                    "gold": { "type": "integer" },
                    "damage": { "type": "integer" }
                },
                "required": ["player_id"]
            }
        },
        "dice_roll_request": {
            "type": "object",
            "description": "Dice roll request details, only present if dice_roll_required is true.",
            "properties": {
                "dice_type": { 
                    "type": "string", 
                    "description": "The type of dice to roll (e.g. 'd20', '2d6')." 
                },
                "reason": { 
                    "type": "string", 
                    "description": "The reason for the dice roll." 
                },
                "ability_modifier": {
                    "type": "string",
                    "description": "The ability to check (e.g. 'strength', 'dexterity', etc.)"
                },
                "proficient": {
                    "type": "boolean",
                    "description": "Whether to apply proficiency bonus"
                },
                "difficulty": {
                    "type": "integer",
                    "description": "The difficulty class (DC) that needs to be met or exceeded for success"
                }
            },
            "required": ["dice_type"]
        }
    },
    "required": ["message", "player_update_required", "dice_roll_required", "combat_started"]
}

# New schema for player updates
PLAYER_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "player_id": { "type": "string" },
        "health_points": { "type": "integer" },
        "gold": { "type": "integer" },
        "damage": { "type": "integer" }
    },
    "required": ["player_id"]
}

# New schema for dice roll requests
DICE_ROLL_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "dice_roll_needed": { "type": "boolean", "description": "Flag indicating if dice roll is needed." },
        "dice_type": { "type": "string", "description": "The type of dice to roll (e.g. 'd20', '2d6'). Use 'd20' for ability check rolls." },
        "ability_modifier": { "type": "string", "description": "The ability to check, e.g., 'charisma', 'strength', etc., if applicable." },
        "proficient": { "type": "boolean", "description": "True if the character is proficient in the relevant ability." },
        "difficulty": { "type": "integer", "description": "The difficulty threshold for the roll." },
        "reason": { "type": "string", "description": "The reason for the dice roll." }
    },
    "required": ["dice_roll_needed", "dice_type", "ability_modifier", "proficient", "difficulty"]
} 