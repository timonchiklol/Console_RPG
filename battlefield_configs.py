"""
Battlefield configurations for different game scenarios.
Each configuration defines a complete battlefield setup including dimensions,
terrain type, and starting positions for player and enemy.
"""

from config import BATTLEFIELD

# Base configuration that others will extend
BASE_CONFIG = {
    "dimensions": BATTLEFIELD["dimensions"],
    "terrain_types": BATTLEFIELD["terrain_types"],
}

BATTLEFIELD_CONFIGS = {
    "forest_ambush": {
        **BASE_CONFIG,
        "name": "Forest Ambush",
        "description": "A dense forest where enemies can hide behind trees. Movement is slower but provides good cover.",
        "default_terrain": "FOREST",
        "dimensions": {
            "cols": 8,
            "rows": 6,
            "hex_size": 40
        },
        "player_start": {"col": 0, "row": 2},
        "enemy_start": {"col": 6, "row": 3},
        "difficulty": "easy"
    },
    "desert_duel": {
        **BASE_CONFIG,
        "name": "Desert Duel",
        "description": "Wide open desert spaces with long sight lines. Perfect for ranged combat.",
        "default_terrain": "DESERT",
        "dimensions": {
            "cols": 12,
            "rows": 8,
            "hex_size": 35
        },
        "player_start": {"col": 1, "row": 4},
        "enemy_start": {"col": 10, "row": 4},
        "difficulty": "medium"
    },
    "cave_encounter": {
        **BASE_CONFIG,
        "name": "Cave Encounter",
        "description": "A dark cave system with tight corridors. Close quarters combat is inevitable.",
        "default_terrain": "CAVE",
        "dimensions": {
            "cols": 6,
            "rows": 10,
            "hex_size": 45
        },
        "player_start": {"col": 2, "row": 0},
        "enemy_start": {"col": 3, "row": 8},
        "difficulty": "hard"
    },
    "winter_siege": {
        **BASE_CONFIG,
        "name": "Winter Siege",
        "description": "A snow-covered battlefield where movement is challenging but visibility is high.",
        "default_terrain": "WINTER",
        "dimensions": {
            "cols": 10,
            "rows": 10,
            "hex_size": 35
        },
        "player_start": {"col": 4, "row": 0},
        "enemy_start": {"col": 5, "row": 9},
        "difficulty": "medium"
    }
} 