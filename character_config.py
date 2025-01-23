from random import randint

RACE_CONFIGS = {
    "Human": {
        "base_hp": 15,
        "base_gold": 5,
        "damage_roll": (2, 7),
        "magic_slots": {"1st": 0, "2nd": 0}
    },
    "Elf": {
        "base_hp": 10,
        "base_gold": 5,
        "damage_roll": (1, 12),
        "magic_slots": {"1st": 0, "2nd": 0}
    },
    "Dwarf": {
        "base_hp": 18,
        "base_gold": 8,
        "damage_roll": (1, 8),
        "magic_slots": {"1st": 0, "2nd": 0}
    },
    "Orc": {
        "base_hp": 8,
        "base_gold": 3,
        "damage_roll": (3, 12),
        "magic_slots": {"1st": 0, "2nd": 0}
    },
    "Halfling": {
        "base_hp": 12,
        "base_gold": 10,
        "damage_roll": (1, 6),
        "magic_slots": {"1st": 0, "2nd": 0}
    },
    "Dragonborn": {
        "base_hp": 14,
        "base_gold": 6,
        "damage_roll": (2, 8),
        "magic_slots": {"1st": 0, "2nd": 0}
    },
    "Tiefling": {
        "base_hp": 12,
        "base_gold": 5,
        "damage_roll": (1, 10),
        "magic_slots": {"1st": 1, "2nd": 0}
    },
    "Gnome": {
        "base_hp": 10,
        "base_gold": 7,
        "damage_roll": (1, 6),
        "magic_slots": {"1st": 2, "2nd": 0}
    }
}

CLASS_CONFIGS = {
    "Warrior": {
        "hp_bonus": 5,
        "gold_bonus": 2,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 0, "2nd": 0}
    },
    "Mage": {
        "hp_bonus": 2,
        "gold_bonus": 1,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 3, "2nd": 1}
    },
    "Ranger": {
        "hp_bonus": 3,
        "gold_bonus": 3,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 1, "2nd": 0}
    },
    "Rogue": {
        "hp_bonus": 2,
        "gold_bonus": 5,
        "damage_bonus": 2,
        "magic_slots_bonus": {"1st": 0, "2nd": 0}
    },
    "Paladin": {
        "hp_bonus": 4,
        "gold_bonus": 2,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 1, "2nd": 0}
    },
    "Warlock": {
        "hp_bonus": 3,
        "gold_bonus": 1,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 2, "2nd": 1}
    },
    "Bard": {
        "hp_bonus": 3,
        "gold_bonus": 4,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 2, "2nd": 0}
    },
    "Cleric": {
        "hp_bonus": 4,
        "gold_bonus": 1,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 2, "2nd": 1}
    },
    "Monk": {
        "hp_bonus": 3,
        "gold_bonus": 1,
        "damage_bonus": 1,
        "magic_slots_bonus": {"1st": 0, "2nd": 0}
    },
    "Druid": {
        "hp_bonus": 3,
        "gold_bonus": 2,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 2, "2nd": 1}
    }
}

ENEMIES = {
    "Goblin": {"hp": 7, "damage": (1,6), "xp": 50, "gold": (1,6)},
    "Skeleton": {"hp": 13, "damage": (1,8), "xp": 100, "gold": (2,8)},
    "Orc": {"hp": 15, "damage": (1,12), "xp": 150, "gold": (2,10)},
    "Wolf": {"hp": 11, "damage": (2,4), "xp": 75, "gold": (0,2)},
    "Bandit": {"hp": 11, "damage": (1,8), "xp": 100, "gold": (4,10)},
    "Zombie": {"hp": 22, "damage": (1,6), "xp": 125, "gold": (0,4)},
    "Dark Cultist": {"hp": 9, "damage": (1,10), "xp": 150, "gold": (3,8)},
    "Giant Spider": {"hp": 10, "damage": (1,8), "xp": 100, "gold": (0,3)}
}

def get_race_stats(race):
    """Get base stats for a race"""
    if race not in RACE_CONFIGS:
        raise ValueError(f"Invalid race: {race}")
    config = RACE_CONFIGS[race]
    return {
        "health_points": config["base_hp"],
        "gold": config["base_gold"],
        "damage": randint(*config["damage_roll"]),
        "magic_1lvl": config["magic_slots"]["1st"],
        "magic_2lvl": config["magic_slots"]["2nd"]
    }

def get_class_bonuses(char_class):
    """Get bonus stats for a class"""
    if char_class not in CLASS_CONFIGS:
        raise ValueError(f"Invalid class: {char_class}")
    config = CLASS_CONFIGS[char_class]
    return {
        "health_points": config["hp_bonus"],
        "gold": config["gold_bonus"],
        "damage": config["damage_bonus"],
        "magic_1lvl": config["magic_slots_bonus"]["1st"],
        "magic_2lvl": config["magic_slots_bonus"]["2nd"]
    }

def get_enemy(enemy_type):
    """Get enemy stats"""
    if enemy_type not in ENEMIES:
        raise ValueError(f"Invalid enemy type: {enemy_type}")
    return ENEMIES[enemy_type].copy() 