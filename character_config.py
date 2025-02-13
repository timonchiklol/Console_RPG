from random import randint

RACE_CONFIGS = {
    "Human": {
        "base_hp": 15,
        "base_gold": 5,
        "damage_roll": (2, 7),
        "magic_slots": {"1st": 0, "2nd": 0},
        "ability_scores": {
            "strength": 1,
            "dexterity": 1,
            "constitution": 1,
            "intelligence": 1,
            "wisdom": 1,
            "charisma": 1
        }
    },
    "Elf": {
        "base_hp": 10,
        "base_gold": 5,
        "damage_roll": (1, 12),
        "magic_slots": {"1st": 0, "2nd": 0},
        "ability_scores": {
            "strength": 0,
            "dexterity": 2,
            "constitution": -1,
            "intelligence": 1,
            "wisdom": 0,
            "charisma": 1
        }
    },
    "Dwarf": {
        "base_hp": 18,
        "base_gold": 8,
        "damage_roll": (1, 8),
        "magic_slots": {"1st": 0, "2nd": 0},
        "ability_scores": {
            "strength": 1,
            "dexterity": -1,
            "constitution": 2,
            "intelligence": 0,
            "wisdom": 1,
            "charisma": 0
        }
    },
    "Orc": {
        "base_hp": 8,
        "base_gold": 3,
        "damage_roll": (3, 12),
        "magic_slots": {"1st": 0, "2nd": 0},
        "ability_scores": {
            "strength": 2,
            "dexterity": 0,
            "constitution": 1,
            "intelligence": -1,
            "wisdom": 0,
            "charisma": -1
        }
    },
    "Halfling": {
        "base_hp": 12,
        "base_gold": 10,
        "damage_roll": (1, 6),
        "magic_slots": {"1st": 0, "2nd": 0},
        "ability_scores": {
            "strength": -1,
            "dexterity": 2,
            "constitution": 0,
            "intelligence": 0,
            "wisdom": 0,
            "charisma": 1
        }
    },
    "Dragonborn": {
        "base_hp": 14,
        "base_gold": 6,
        "damage_roll": (2, 8),
        "magic_slots": {"1st": 0, "2nd": 0},
        "ability_scores": {
            "strength": 2,
            "dexterity": 0,
            "constitution": 0,
            "intelligence": 0,
            "wisdom": 0,
            "charisma": 1
        }
    },
    "Tiefling": {
        "base_hp": 12,
        "base_gold": 5,
        "damage_roll": (1, 10),
        "magic_slots": {"1st": 1, "2nd": 0},
        "ability_scores": {
            "strength": 0,
            "dexterity": 0,
            "constitution": 0,
            "intelligence": 1,
            "wisdom": 0,
            "charisma": 2
        }
    },
    "Gnome": {
        "base_hp": 10,
        "base_gold": 7,
        "damage_roll": (1, 6),
        "magic_slots": {"1st": 2, "2nd": 0},
        "ability_scores": {
            "strength": -1,
            "dexterity": 0,
            "constitution": 0,
            "intelligence": 2,
            "wisdom": 0,
            "charisma": 1
        }
    }
}

CLASS_CONFIGS = {
    "Warrior": {
        "hp_bonus": 5,
        "gold_bonus": 2,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 0, "2nd": 0},
        "primary_ability": "strength",
        "saving_throws": ["strength", "constitution"]
    },
    "Mage": {
        "hp_bonus": 2,
        "gold_bonus": 1,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 3, "2nd": 1},
        "primary_ability": "intelligence",
        "saving_throws": ["intelligence", "wisdom"]
    },
    "Ranger": {
        "hp_bonus": 3,
        "gold_bonus": 3,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 1, "2nd": 0},
        "primary_ability": "dexterity",
        "saving_throws": ["dexterity", "wisdom"]
    },
    "Rogue": {
        "hp_bonus": 2,
        "gold_bonus": 5,
        "damage_bonus": 2,
        "magic_slots_bonus": {"1st": 0, "2nd": 0},
        "primary_ability": "dexterity",
        "saving_throws": ["dexterity", "intelligence"]
    },
    "Paladin": {
        "hp_bonus": 4,
        "gold_bonus": 2,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 1, "2nd": 0},
        "primary_ability": "strength",
        "saving_throws": ["wisdom", "charisma"]
    },
    "Warlock": {
        "hp_bonus": 3,
        "gold_bonus": 1,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 2, "2nd": 1},
        "primary_ability": "charisma",
        "saving_throws": ["wisdom", "charisma"]
    },
    "Bard": {
        "hp_bonus": 3,
        "gold_bonus": 4,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 2, "2nd": 0},
        "primary_ability": "charisma",
        "saving_throws": ["dexterity", "charisma"]
    },
    "Cleric": {
        "hp_bonus": 4,
        "gold_bonus": 1,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 2, "2nd": 1},
        "primary_ability": "wisdom",
        "saving_throws": ["wisdom", "charisma"]
    },
    "Monk": {
        "hp_bonus": 3,
        "gold_bonus": 1,
        "damage_bonus": 1,
        "magic_slots_bonus": {"1st": 0, "2nd": 0},
        "primary_ability": "dexterity",
        "saving_throws": ["strength", "dexterity"]
    },
    "Druid": {
        "hp_bonus": 3,
        "gold_bonus": 2,
        "damage_bonus": 0,
        "magic_slots_bonus": {"1st": 2, "2nd": 1},
        "primary_ability": "wisdom",
        "saving_throws": ["intelligence", "wisdom"]
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

RACE_TRANSLATIONS = {
    'en': {
        'Human': 'Human',
        'Elf': 'Elf',
        'Dwarf': 'Dwarf',
        'Orc': 'Orc',
        'Halfling': 'Halfling',
        'Dragonborn': 'Dragonborn',
        'Tiefling': 'Tiefling',
        'Gnome': 'Gnome'
    },
    'ru': {
        'Human': 'Человек',
        'Elf': 'Эльф',
        'Dwarf': 'Гном',
        'Orc': 'Орк',
        'Halfling': 'Полурослик',
        'Dragonborn': 'Драконорожденный',
        'Tiefling': 'Тифлинг',
        'Gnome': 'Гном'
    }
}

CLASS_TRANSLATIONS = {
    'en': {
        'Warrior': 'Warrior',
        'Mage': 'Mage',
        'Ranger': 'Ranger',
        'Rogue': 'Rogue',
        'Paladin': 'Paladin',
        'Warlock': 'Warlock',
        'Bard': 'Bard',
        'Cleric': 'Cleric',
        'Monk': 'Monk',
        'Druid': 'Druid'
    },
    'ru': {
        'Warrior': 'Воин',
        'Mage': 'Маг',
        'Ranger': 'Следопыт',
        'Rogue': 'Плут',
        'Paladin': 'Паладин',
        'Warlock': 'Колдун',
        'Bard': 'Бард',
        'Cleric': 'Жрец',
        'Monk': 'Монах',
        'Druid': 'Друид'
    }
}

RACE_STATS = {
    'Human': {'hp': 15, 'damage': '2-7', 'gold': 5},
    'Elf': {'hp': 10, 'damage': '1-12', 'gold': 5},
    'Dwarf': {'hp': 18, 'damage': '1-8', 'gold': 8},
    'Orc': {'hp': 8, 'damage': '3-12', 'gold': 3},
    'Halfling': {'hp': 12, 'damage': '1-6', 'gold': 10},
    'Dragonborn': {'hp': 14, 'damage': '2-8', 'gold': 6},
    'Tiefling': {'hp': 12, 'damage': '1-10', 'gold': 5},
    'Gnome': {'hp': 10, 'damage': '1-6', 'gold': 7}
}

CLASS_BONUSES = {
    'Warrior': {'hp_bonus': 5, 'gold_bonus': 2, 'magic': 0},
    'Mage': {'hp_bonus': 2, 'gold_bonus': 1, 'magic': 3},
    'Ranger': {'hp_bonus': 3, 'gold_bonus': 3, 'magic': 1},
    'Rogue': {'hp_bonus': 2, 'gold_bonus': 5, 'magic': 0},
    'Paladin': {'hp_bonus': 4, 'gold_bonus': 2, 'magic': 1},
    'Warlock': {'hp_bonus': 3, 'gold_bonus': 1, 'magic': 2},
    'Bard': {'hp_bonus': 3, 'gold_bonus': 4, 'magic': 2},
    'Cleric': {'hp_bonus': 4, 'gold_bonus': 1, 'magic': 2},
    'Monk': {'hp_bonus': 3, 'gold_bonus': 1, 'magic': 0},
    'Druid': {'hp_bonus': 3, 'gold_bonus': 2, 'magic': 2}
}

ENEMIES = {
    'Goblin': {'hp': 10, 'damage': (1, 4), 'gold': (1, 4), 'xp': 50},
    'Orc': {'hp': 15, 'damage': (2, 8), 'gold': (2, 6), 'xp': 100},
    'Troll': {'hp': 30, 'damage': (3, 10), 'gold': (4, 10), 'xp': 200},
    'Dragon': {'hp': 50, 'damage': (4, 12), 'gold': (10, 20), 'xp': 500}
}

def get_race_stats(race_name):
    """Get race stats, handling translations"""
    # Convert localized name to English if needed
    for lang in RACE_TRANSLATIONS.values():
        for eng_name, local_name in lang.items():
            if local_name == race_name:
                race_name = eng_name
                break
    return RACE_STATS.get(race_name, RACE_STATS['Human'])

def get_class_bonuses(class_name):
    """Get class bonuses, handling translations"""
    # Convert localized name to English if needed
    for lang in CLASS_TRANSLATIONS.values():
        for eng_name, local_name in lang.items():
            if local_name == class_name:
                class_name = eng_name
                break
    return CLASS_BONUSES.get(class_name, CLASS_BONUSES['Warrior'])

def get_enemy(enemy_type):
    """Get a copy of enemy stats"""
    return ENEMIES.get(enemy_type, ENEMIES['Goblin']).copy()

def calculate_ability_modifier(score):
    """Calculate the ability score modifier using D&D 5e rules"""
    return (score - 10) // 2

def roll_with_modifier(dice_count, dice_sides, ability_score):
    """Roll dice and add ability modifier"""
    total = sum(randint(1, dice_sides) for _ in range(dice_count))
    modifier = calculate_ability_modifier(ability_score)
    return total + modifier

def get_attack_roll(character_race, character_class, ability_scores):
    """Calculate attack roll based on character's race, class and relevant ability score"""
    race_config = RACE_CONFIGS[character_race]
    class_config = CLASS_CONFIGS[character_class]
    
    # Get primary ability for the class
    primary_ability = class_config["primary_ability"]
    
    # Calculate total ability score
    total_ability_score = ability_scores[primary_ability] + race_config["ability_scores"][primary_ability]
    
    # Get base damage roll
    dice_count, dice_sides = race_config["damage_roll"]
    
    # Roll with ability modifier
    damage = roll_with_modifier(dice_count, dice_sides, total_ability_score)
    
    # Add class damage bonus
    damage += class_config["damage_bonus"]
    
    return damage

def get_saving_throw(character_race, character_class, ability_scores, ability):
    """Calculate saving throw for a given ability"""
    race_config = RACE_CONFIGS[character_race]
    class_config = CLASS_CONFIGS[character_class]
    
    # Calculate total ability score
    total_ability_score = ability_scores[ability] + race_config["ability_scores"][ability]
    
    # Calculate base modifier
    modifier = calculate_ability_modifier(total_ability_score)
    
    # Add proficiency bonus if the class is proficient in this saving throw
    if ability in class_config["saving_throws"]:
        modifier += 2  # Base proficiency bonus
        
    return modifier 