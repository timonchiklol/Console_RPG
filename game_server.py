from flask import Flask, render_template, request, jsonify, session
import os
import json
import random
import logging
from battlefield_configs import BATTLEFIELD_CONFIGS
from config import GAME_RULES, PLAYER, ENEMIES
from character_config import RACE_CONFIGS, CLASS_CONFIGS
import dnd_spells

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dnd_battlefield_secret_key")

# Add mana to each race
for race_name, race_config in RACE_CONFIGS.items():
    # Calculate mana based on intelligence and wisdom
    base_intelligence = race_config["ability_scores"].get("intelligence", 0)
    base_wisdom = race_config["ability_scores"].get("wisdom", 0)
    race_config["base_mana"] = 20 + (base_intelligence * 2) + base_wisdom
    race_config["max_mana"] = race_config["base_mana"]

# Add mana costs to spells
spell_mana_costs = {
    "1": 5,  # Level 1 spells cost 5 mana
    "2": 10  # Level 2 spells cost 10 mana
}

# Add mana costs to each spell
for spell_name, spell_data in dnd_spells.spells_1lvl.items():
    spell_data["mana_cost"] = spell_mana_costs["1"]

for spell_name, spell_data in dnd_spells.spells_2lvl.items():
    spell_data["mana_cost"] = spell_mana_costs["2"]

@app.route('/')
def index():
    """Render the main landing page"""
    battlefield_configs = {
        name: {
            'name': config['name'],
            'description': config['description'],
            'difficulty': config.get('difficulty', 'medium')
        } for name, config in BATTLEFIELD_CONFIGS.items()
    }
    
    races = {name: {'description': f"A {name.lower()} character"} for name in RACE_CONFIGS.keys()}
    classes = {name: {'description': f"A {name.lower()} class"} for name in CLASS_CONFIGS.keys()}
    
    return render_template(
        'battle_index.html', 
        battlefield_configs=battlefield_configs,
        races=races,
        classes=classes
    )

@app.route('/battle')
def battle():
    """Render the battle page"""
    battlefield = request.args.get('battlefield', 'forest_ambush')
    race = request.args.get('race', 'Human')
    character_class = request.args.get('class', 'Warrior')
    
    # Store selections in session
    session['battlefield'] = battlefield
    session['race'] = race
    session['class'] = character_class
    
    # Get battlefield config
    battlefield_config = BATTLEFIELD_CONFIGS.get(battlefield, BATTLEFIELD_CONFIGS['forest_ambush'])
    
    # Get character stats
    race_config = RACE_CONFIGS.get(race, RACE_CONFIGS['Human'])
    class_config = CLASS_CONFIGS.get(character_class, CLASS_CONFIGS['Warrior'])
    
    # Calculate player stats
    player_stats = calculate_player_stats(race_config, class_config)
    
    # Get enemy based on difficulty
    enemy_type = get_enemy_for_difficulty(battlefield_config.get('difficulty', 'medium'))
    enemy_stats = ENEMIES.get(enemy_type, ENEMIES['goblin'])
    
    # Pass all data to the template
    return render_template(
        'battle_field.html',
        battlefield_config=battlefield_config,
        player_stats=player_stats,
        enemy_stats=enemy_stats,
        spells_1lvl=dnd_spells.spells_1lvl,
        spells_2lvl=dnd_spells.spells_2lvl,
        basic_attacks=dnd_spells.basic_attacks,
        game_rules=GAME_RULES,
        spell_mana_costs=spell_mana_costs
    )

@app.route('/api/roll_dice', methods=['POST'])
def roll_dice():
    """API endpoint to roll dice"""
    data = request.json
    dice_notation = data.get('dice')
    
    if not dice_notation:
        return jsonify({'error': 'Dice notation required'}), 400
    
    # Parse dice notation like '2d6+3'
    dice_parts = dice_notation.lower().replace(' ', '').split('d')
    
    if len(dice_parts) != 2:
        return jsonify({'error': 'Invalid dice notation'}), 400
    
    try:
        num_dice = int(dice_parts[0]) if dice_parts[0] else 1
        
        # Handle modifiers like +3
        sides_parts = dice_parts[1].split('+')
        if len(sides_parts) > 1:
            sides = int(sides_parts[0])
            modifier = int(sides_parts[1])
        else:
            sides = int(dice_parts[1])
            modifier = 0
        
        # Roll the dice
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        return jsonify({
            'rolls': rolls,
            'total': total,
            'modifier': modifier
        })
    
    except ValueError:
        return jsonify({'error': 'Invalid dice notation format'}), 400

@app.route('/api/check_hit', methods=['POST'])
def check_hit():
    """API endpoint to check if an attack hits"""
    data = request.json
    roll = random.randint(1, 20)
    hit = roll > 10  # Simple hit check, natural 11+ hits
    
    return jsonify({
        'roll': roll,
        'hit': hit,
        'critical': roll == 20  # Natural 20 is critical hit
    })

@app.route('/api/enemy_turn', methods=['POST'])
def enemy_turn():
    """API endpoint to handle enemy turn"""
    data = request.json
    player_position = data.get('player_position', {'col': 2, 'row': 5})
    enemy_position = data.get('enemy_position', {'col': 8, 'row': 5})
    enemy_type = data.get('enemy_type', 'goblin')
    
    # Get enemy config
    enemy_config = ENEMIES.get(enemy_type, ENEMIES['goblin'])
    
    # If enemy is close to player, attack, otherwise move toward player
    enemy_col, enemy_row = enemy_position['col'], enemy_position['row']
    player_col, player_row = player_position['col'], player_position['row']
    
    # Calculate distance
    distance = calculate_distance(enemy_col, enemy_row, player_col, player_row)
    
    result = {
        'action': None,
        'new_position': enemy_position,
        'attack_result': None,
        'message': None
    }
    
    # Check if the enemy can attack
    can_attack = False
    attack_ability = None
    
    for ability_name, ability in enemy_config['abilities'].items():
        if distance <= ability['range']:
            can_attack = True
            attack_ability = ability
            break
    
    if can_attack:
        # Enemy attacks
        roll = random.randint(1, 20)
        hit = roll > 10
        
        # Calculate damage if hit
        damage = 0
        damage_rolls = []
        
        if hit:
            damage_dice = attack_ability['damage'].split('d')
            dice_count = int(damage_dice[0])
            dice_sides = int(damage_dice[1])
            
            damage_rolls = [random.randint(1, dice_sides) for _ in range(dice_count)]
            damage = sum(damage_rolls)
        
        result['action'] = 'attack'
        result['attack_result'] = {
            'ability_name': attack_ability['name'],
            'roll': roll,
            'hit': hit,
            'damage': damage,
            'damage_rolls': damage_rolls
        }
        result['message'] = f"Enemy attacks with {attack_ability['name']}"
        if hit:
            result['message'] += f" and hits for {damage} damage!"
        else:
            result['message'] += " but misses!"
    else:
        # Enemy moves toward player
        new_position = move_toward_player(enemy_position, player_position, enemy_config['stats']['speed'])
        
        result['action'] = 'move'
        result['new_position'] = new_position
        result['message'] = f"Enemy moves toward you"
    
    # Restore some mana for the enemy (if applicable)
    if 'mana' in enemy_config['stats']:
        enemy_config['stats']['mana'] = min(
            enemy_config['stats']['mana'] + 5,
            enemy_config['stats'].get('max_mana', 0)
        )
    
    return jsonify(result)

def calculate_player_stats(race_config, class_config):
    """Calculate player stats based on race and class"""
    # Start with base stats
    stats = {
        'hp': race_config['base_hp'] + class_config['hp_bonus'],
        'max_hp': race_config['base_hp'] + class_config['hp_bonus'],
        'mana': race_config['base_mana'],
        'max_mana': race_config['max_mana'],
        'speed': 30,  # Default speed
    }
    
    # Add ability scores
    default_stats = class_config['default_stats']
    
    for ability, value in default_stats.items():
        stats[ability] = value + race_config['ability_scores'].get(ability, 0)
    
    # Calculate magic slots
    magic_slots = {}
    for level, count in race_config['magic_slots'].items():
        magic_slots[level] = count + class_config['magic_slots_bonus'].get(level, 0)
    
    stats['magic_slots'] = magic_slots
    
    return stats

def get_enemy_for_difficulty(difficulty):
    """Return an appropriate enemy based on difficulty"""
    if difficulty == 'easy':
        return 'goblin'
    elif difficulty == 'hard':
        return 'orc'
    else:  # medium
        return random.choice(['goblin', 'orc'])

def calculate_distance(col1, row1, col2, row2):
    """Calculate the distance between two hex grid cells"""
    dx = abs(col1 - col2)
    dy = abs(row1 - row2)
    return max(dx, dy)

def move_toward_player(enemy_pos, player_pos, speed):
    """Move the enemy toward the player"""
    enemy_col, enemy_row = enemy_pos['col'], enemy_pos['row']
    player_col, player_row = player_pos['col'], player_pos['row']
    
    # Simple movement logic: move toward player
    if enemy_col < player_col:
        enemy_col += 1
    elif enemy_col > player_col:
        enemy_col -= 1
        
    if enemy_row < player_row:
        enemy_row += 1
    elif enemy_row > player_row:
        enemy_row -= 1
    
    return {'col': enemy_col, 'row': enemy_row}

if __name__ == '__main__':
    app.run(debug=True, port=5001) 