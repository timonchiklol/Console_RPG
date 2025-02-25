"""
Configuration file for the Console RPG game.
Contains settings for battlefield, characters, and game rules.
"""

# Battlefield Configuration
BATTLEFIELD = {
    "dimensions": {
        "cols": 15,
        "rows": 12,
        "hex_size": 30
    },
    "terrain_types": {
        "CAVE": {
            "grid_color": "#3d3d3d",
            "hex_fill": {
                "colors": ["#4a4a4a", "#545454", "#404040", "#4d4d4d"],
                "frequency": 0.7
            },
            "movement_cost": 1.0  # Movement costs more in caves
        },
        "FOREST": {
            "grid_color": "#2d5a27",
            "hex_fill": {
                "colors": ["#2d5a27", "#1e4d2b", "#386641", "#1b4332"],
                "frequency": 0.8
            },
            "movement_cost": 1.0  # Movement costs more in forests
        },
        "DESERT": {
            "grid_color": "#b38b6d",
            "hex_fill": {
                "colors": ["#deb887", "#d2aa7d", "#c4976f", "#b38b6d"],
                "frequency": 0.9
            },
            "movement_cost": 1.2  # Movement costs more in desert
        },
        "WINTER": {
            "grid_color": "#b3d4d6",
            "hex_fill": {
                "colors": ["#ffffff", "#f0f8ff", "#e6f3ff", "#d6eaff"],
                "frequency": 0.6
            },
            "movement_cost": 1.0  # Movement costs more in winter
        }
    },
    "default_terrain": "FOREST"
}

# Player Configuration
PLAYER = {
    "starting_position": {
        "col": 0,
        "row": 0
    },
    "stats": {
        "hp": 100,
        "max_hp": 100,
        "speed": 30,
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10
    },
    "spell_slots": {
        "1": 4,  # Level 1 spell slots
        "2": 2   # Level 2 spell slots
    },
    "abilities": {
        "melee_attack": {
            "name": "Melee Attack",
            "damage": "1d6",
            "range": 1,
            "description": "Basic melee attack"
        }
    }
}

# Enemy Configuration
ENEMIES = {
    "goblin": {
        "name": "Goblin",
        "stats": {
            "hp": 75,
            "max_hp": 75,
            "speed": 25,
            "strength": 8,
            "dexterity": 14,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 8,
            "charisma": 8
        },
        "position": {
            "col": 5,
            "row": 4
        },
        "abilities": {
            "bow_attack": {
                "name": "Bow Attack",
                "damage": "1d6",
                "range": 4,
                "description": "Shoots an arrow"
            },
            "melee_attack": {
                "name": "Melee Attack",
                "damage": "1d8",
                "range": 1,
                "description": "Strikes with fists"
            }
        }
    },
    "orc": {
        "name": "Orc",
        "stats": {
            "hp": 100,
            "max_hp": 100,
            "speed": 20,
            "strength": 16,
            "dexterity": 12,
            "constitution": 16,
            "intelligence": 7,
            "wisdom": 11,
            "charisma": 10
        },
        "position": {
            "col": 4,
            "row": 4
        },
        "abilities": {
            "greataxe": {
                "name": "Greataxe",
                "damage": "1d12",
                "range": 1,
                "description": "Swings a mighty greataxe"
            },
            "javelin": {
                "name": "Javelin",
                "damage": "1d6",
                "range": 3,
                "description": "Throws a javelin"
            }
        }
    }
}

# Game Rules Configuration
GAME_RULES = {
    "movement": {
        "base_cost": 5,  # Base cost of 5 for all hexes
        "terrain_costs": {
            "plains": 5,
            "forest": 7,
            "mountains": 10,
            "desert": 6,
            "water": 8
        },
        "diagonal_cost": 5,  # Changed to match base_cost to avoid extra cost
        "min_movement": 4,
    },
    "combat": {
        "attack_cost": 0,
        "spell_cost": 0,
        "opportunity_attack_range": 1  # Range for opportunity attacks
    },
    "effects": {
        "burning": {
            "damage": 2,
            "duration": 3,
            "breaks_control": True
        },
        "frozen": {
            "movement_penalty": 3,
            "duration": 2,
            "breaks_on_damage": True
        },
        "stunned": {
            "duration": 1,
            "breaks_on_damage": False
        }
    }
} 