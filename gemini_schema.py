from pydantic import BaseModel
from typing import Optional, List, Dict, Union

class GameState(BaseModel):
    health_points: int
    gold: int
    damage: int
    in_combat: bool
    enemy_health: Optional[int] = None
    dice_roll_needed: bool = False
    dice_type: Optional[str] = None  # e.g. "d20", "2d6", etc.

# Define the schema as a dictionary that matches Gemini's expected format
GAME_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "message": {
            "type": "STRING",
            "description": "The message from the DM to the player"
        },
        "state_update": {
            "type": "OBJECT",
            "properties": {
                "health_points": {"type": "INTEGER"},
                "gold": {"type": "INTEGER"},
                "damage": {"type": "INTEGER"},
                "in_combat": {"type": "BOOLEAN"},
                "enemy_health": {"type": "INTEGER"},
                "dice_roll_needed": {"type": "BOOLEAN"},
                "dice_type": {"type": "STRING", "description": "The type of dice to roll (e.g., 'd20', '2d6')"}
            },
            "required": ["health_points", "gold", "damage", "in_combat"]
        },
        "combat_result": {
            "type": "OBJECT",
            "properties": {
                "damage_dealt": {"type": "INTEGER"},
                "damage_taken": {"type": "INTEGER"},
                "outcome": {"type": "STRING"}
            }
        },
        "required_action": {
            "type": "STRING",
            "description": "The type of action required from the player",
            "enum": ["roll_dice", "make_choice", "none"]
        },
        "dice_roll": {
            "type": "OBJECT",
            "properties": {
                "required": {"type": "BOOLEAN"},
                "type": {"type": "STRING", "description": "The type of dice to roll (e.g., 'd20', '2d6')"},
                "reason": {"type": "STRING", "description": "Why the dice roll is needed"}
            }
        }
    },
    "required": ["message"]
} 