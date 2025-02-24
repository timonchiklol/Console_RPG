from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import math
from dnd_spells import spells_1lvl, spells_2lvl, basic_attacks
from gemini import Gemini
from dotenv import load_dotenv
import os
from config import BATTLEFIELD, PLAYER, ENEMIES, GAME_RULES  # Import our new config

app = Flask(__name__)
app.secret_key = 'secret-key-for-session'

# Load environment variables
load_dotenv()

# Initialize Gemini AI with updated enemy configuration
gemini = Gemini(
    API_KEY=os.getenv('GEMINI_API_KEY'),
    system_instruction=f"""You are a D&D combat AI controlling a enemy.
Your goal is to make tactical decisions based on position and range.
The enemy has these attacks:
{ENEMIES['goblin']['abilities']}

Choose the best action based on:
1. Distance to player
2. Current HP
3. Tactical advantage

Respond with a JSON object containing:
{{
    "action": "move/attack",
    "target_position": {{"col": x, "row": y}},
    "attack_type": "attack_name",
    "combat_log": "Description of enemy's actions"
}}
"""
)

def get_neighbors(cell):
    """Get neighboring cells. Accepts either a tuple (col, row) or a dict with col/row keys"""
    # Handle both tuple and dict formats
    if isinstance(cell, tuple):
        col, row = cell
    else:
        col, row = cell[0], cell[1]
        
    if col % 2 == 0:
        neighbors = [(col, row-1), (col, row+1), (col+1, row-1), (col+1, row), (col-1, row-1), (col-1, row)]
    else:
        neighbors = [(col, row-1), (col, row+1), (col+1, row), (col+1, row+1), (col-1, row), (col-1, row+1)]
    return [(c, r) for (c, r) in neighbors if 0 <= c < BATTLEFIELD['dimensions']['cols'] and 0 <= r < BATTLEFIELD['dimensions']['rows']]

def compute_path(start_col, start_row, target_col, target_row, max_steps=None):
    """Compute path from start to target using BFS, limited by max_steps"""
    queue = [(start_col, start_row, [])]
    visited = {(start_col, start_row)}
    best_path = []
    min_distance = float('inf')
    
    while queue:
        col, row, path = queue.pop(0)
        
        # Calculate distance to target
        dx = col - target_col
        dy = row - target_row
        dist = math.sqrt(dx * dx + dy * dy)
        
        # Update best path if this is closer to target
        if dist < min_distance:
            min_distance = dist
            best_path = path + [(col, row)]
        
        if max_steps is not None and len(path) >= max_steps:
            continue
            
        if (col, row) == (target_col, target_row):
            return path
            
        for next_col, next_row in get_neighbors((col, row)):
            if (next_col, next_row) not in visited and (next_col, next_row) != (target_col, target_row):
                visited.add((next_col, next_row))
                new_path = path + [(next_col, next_row)]
                queue.append((next_col, next_row, new_path))
    
    return best_path

@app.route("/", methods=["GET", "POST"])
def character_creation():
    if request.method == "POST":
        name = request.form.get("name", "Adventurer")
        
        # Initialize character from config
        character = {
            'name': name,
            'hp': PLAYER['stats']['hp'],
            'max_hp': PLAYER['stats']['max_hp'],
            'speed': PLAYER['stats']['speed'],
            'movement_left': PLAYER['stats']['speed'],
            'spell_slots': PLAYER['spell_slots'].copy(),
            'pos': PLAYER['starting_position'].copy(),
            'abilities': PLAYER['abilities'].copy(),  # Add abilities from config
            'ability_scores': {
                'strength': int(request.form.get('strength', PLAYER['stats']['strength'])),
                'dexterity': int(request.form.get('dexterity', PLAYER['stats']['dexterity'])),
                'constitution': int(request.form.get('constitution', PLAYER['stats']['constitution'])),
                'intelligence': int(request.form.get('intelligence', PLAYER['stats']['intelligence'])),
                'wisdom': int(request.form.get('wisdom', PLAYER['stats']['wisdom'])),
                'charisma': int(request.form.get('charisma', PLAYER['stats']['charisma']))
            }
        }
        
        # Initialize enemy from config (using goblin as default)
        enemy_type = 'goblin'
        enemy = {
            'name': ENEMIES[enemy_type]['name'],
            'hp': ENEMIES[enemy_type]['stats']['hp'],
            'max_hp': ENEMIES[enemy_type]['stats']['max_hp'],
            'speed': ENEMIES[enemy_type]['stats']['speed'],
            'movement_left': ENEMIES[enemy_type]['stats']['speed'],
            'pos': ENEMIES[enemy_type]['position'].copy(),
            'abilities': ENEMIES[enemy_type]['abilities'].copy()
        }
        
        # Save to session
        session['character'] = character
        session['enemy'] = enemy
        session['effects'] = {
            'enemy': {},  # effects on enemy
            'player': {}  # effects on player
        }
        session['current_terrain'] = BATTLEFIELD['default_terrain']
        
        return redirect(url_for("battle"))
    return render_template("create.html")

@app.route("/battle", methods=["GET"])
def battle():
    if 'character' not in session:
        return redirect(url_for('character_creation'))
    
    # Initialize enemy if not exists
    if 'enemy' not in session:
        enemy_type = 'goblin'
        session['enemy'] = {
            'name': ENEMIES[enemy_type]['name'],
            'hp': ENEMIES[enemy_type]['stats']['hp'],
            'max_hp': ENEMIES[enemy_type]['stats']['max_hp'],
            'speed': ENEMIES[enemy_type]['stats']['speed'],
            'movement_left': ENEMIES[enemy_type]['stats']['speed'],
            'pos': ENEMIES[enemy_type]['position'].copy(),
            'abilities': ENEMIES[enemy_type]['abilities'].copy()
        }
    
    # Initialize effects if not exists
    if 'effects' not in session:
        session['effects'] = {
            'enemy': {},
            'player': {}
        }
    
    # Initialize terrain if not exists
    if 'current_terrain' not in session:
        session['current_terrain'] = BATTLEFIELD['default_terrain']
    
    return render_template('battle.html', 
        character=session['character'],
        enemy=session['enemy'],
        spells_1lvl=spells_1lvl,
        spells_2lvl=spells_2lvl,
        basic_attacks=basic_attacks,
        battlefield_config=BATTLEFIELD,
        current_terrain=session['current_terrain'],
        game_rules=GAME_RULES,
        lang='en'
    )

# Add new roll_dice endpoint
@app.route("/api/roll_dice", methods=["POST"])
def roll_dice():
    sides = int(request.form.get("sides", 6))
    result = random.randint(1, sides)
    return jsonify({"result": result})

# Update attack endpoint to use manual dice rolls
@app.route("/api/attack", methods=["POST"])
def api_attack():
    if 'character' not in session or 'enemy' not in session:
        return jsonify({"error": "No battle in progress."})
    
    character = session['character']
    enemy = session['enemy']
    
    # Get attack type from request
    attack_type = request.form.get("attack_type", "melee_attack")
    
    # Get the attack configuration
    if attack_type in PLAYER['abilities']:
        attack_config = PLAYER['abilities'][attack_type]
    else:
        return jsonify({"error": "Invalid attack type"})
    
    # Check if we have enough speed for the attack
    attack_cost = GAME_RULES['combat']['attack_cost']
    if character['movement_left'] < attack_cost:
        return jsonify({"error": "Not enough speed for attack"})
    
    hit_roll = request.form.get("hit_roll")
    damage_roll = request.form.get("damage_roll")
    
    if hit_roll is not None and damage_roll is not None:
        hit_roll = int(hit_roll)
        damage_roll = int(damage_roll)
        if hit_roll >= 10:  # TODO: Use proper AC calculation
            enemy['hp'] -= damage_roll
            combat_log = f"You used {attack_config['name']} and dealt {damage_roll} damage."
        else:
            combat_log = f"Your {attack_config['name']} missed!"
    else:
        # Fallback auto-roll if manual roll not provided
        roll = random.randint(1, 20)
        if roll >= 10:  # TODO: Use proper AC calculation
            # Parse damage dice (e.g., "1d6")
            dice_count, dice_sides = map(int, attack_config['damage'].split('d'))
            damage = sum(random.randint(1, dice_sides) for _ in range(dice_count))
            enemy['hp'] -= damage
            combat_log = f"You used {attack_config['name']} and dealt {damage} damage."
        else:
            combat_log = f"Your {attack_config['name']} missed!"
    
    # Deduct speed cost
    character['movement_left'] -= attack_cost
    
    session['character'] = character
    session['enemy'] = enemy
    
    return jsonify({
        "combat_log": combat_log,
        "character_hp": character['hp'],
        "enemy_hp": enemy['hp'],
        "enemy_defeated": enemy['hp'] <= 0,
        "movement_left": character['movement_left']
    })

# Обновляем функцию api_enemy_attack, добавляем обработку новых эффектов
@app.route("/api/enemy_attack", methods=["POST"])
def api_enemy_attack():
    try:
        character = session.get('character', {})
        enemy = session.get('enemy', {})
        effects = session.get('effects', {'enemy': {}, 'player': {}})
        combat_log = ""
        
        # Check effects on enemy
        enemy_effects = effects['enemy']
        
        # Process damage from effects
        if 'burning' in enemy_effects:
            damage = GAME_RULES['effects']['burning']['damage']
            enemy['hp'] -= damage
            combat_log += f"Enemy takes {damage} damage from burning! "
            
            # Check if Hold Person effect should break
            if 'paralyze' in enemy_effects and GAME_RULES['effects']['paralyze']['breaks_on_damage']:
                del enemy_effects['paralyze']
                combat_log += "Hold Person effect breaks from damage! "
        
        if 'bleeding' in enemy_effects:
            damage = GAME_RULES['effects'].get('bleeding', {}).get('damage', 1)
            enemy['hp'] -= damage
            combat_log += f"Enemy takes {damage} damage from bleeding! "
            
            # Check Hold Person
            if 'paralyze' in enemy_effects and GAME_RULES['effects']['paralyze']['breaks_on_damage']:
                del enemy_effects['paralyze']
                combat_log += "Hold Person effect breaks from damage! "
        
        # Check if enemy is under control effects
        if any(effect in enemy_effects for effect in ['paralyze', 'frozen', 'fear', 'stunned']):
            if 'fear' in enemy_effects:
                # Use enemy's own attack against itself
                enemy_type = enemy.get('name', 'goblin').lower()
                attack = list(ENEMIES[enemy_type]['abilities'].values())[0]
                dice_count, dice_sides = map(int, attack['damage'].split('d'))
                damage = sum(random.randint(1, dice_sides) for _ in range(dice_count))
                enemy['hp'] -= damage
                combat_log += f"Enemy is feared and attacks itself for {damage} damage! "
            elif 'frozen' in enemy_effects:
                combat_log += "Enemy is frozen and cannot act! "
            elif 'stunned' in enemy_effects:
                combat_log += "Enemy is stunned and cannot attack! "
            else:
                combat_log += "Enemy is paralyzed and cannot move or attack! "
            
            # Reduce effect durations
            for effect_name in list(enemy_effects.keys()):
                effect = enemy_effects[effect_name]
                effect['duration'] -= 1
                if effect['duration'] <= 0:
                    del enemy_effects[effect_name]
                    combat_log += f"Enemy is no longer {effect_name}! "
            
            effects['enemy'] = enemy_effects
            session['effects'] = effects
            session['enemy'] = enemy
            session.modified = True
            
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": enemy['hp'],
                "enemy_pos": enemy['pos']
            })
        
        # Normal attack if no control effects
        enemy_type = enemy.get('name', 'goblin').lower()
        available_attacks = ENEMIES[enemy_type]['abilities']
        
        # Choose attack based on range to player
        player_pos = character['pos']
        enemy_pos = enemy['pos']
        distance = math.sqrt((player_pos['col'] - enemy_pos['col'])**2 + 
                           (player_pos['row'] - enemy_pos['row'])**2)
        
        # Select best attack based on range
        selected_attack = None
        for attack in available_attacks.values():
            if attack['range'] >= distance:
                selected_attack = attack
                break
        
        if not selected_attack:
            combat_log += "Enemy is too far to attack!"
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": enemy['hp'],
                "enemy_pos": enemy['pos']
            })
        
        # Roll attack
        roll = random.randint(1, 20)
        if roll >= 10:  # TODO: Use proper AC calculation
            dice_count, dice_sides = map(int, selected_attack['damage'].split('d'))
            damage = sum(random.randint(1, dice_sides) for _ in range(dice_count))
            character['hp'] -= damage
            combat_log += f"Enemy uses {selected_attack['name']} and deals {damage} damage! "
        else:
            combat_log += f"Enemy's {selected_attack['name']} missed! "
        
        session['character'] = character
        session['enemy'] = enemy
        session['effects'] = effects
        session.modified = True
        
        return jsonify({
            "combat_log": combat_log,
            "character_hp": character['hp'],
            "enemy_hp": enemy['hp'],
            "enemy_pos": enemy['pos']
        })
        
    except Exception as e:
        print(f"Error in enemy attack: {e}")
        return jsonify({"error": f"Enemy attack error: {str(e)}"})

# Обновляем функцию api_cast_spell для новых эффектов
@app.route("/api/cast_spell", methods=["POST"])
def api_cast_spell():
    try:
        data = request.get_json()
        spell_name = data.get('spell_name')
        target = data.get('target', {})
        
        character = session['character']
        enemy = session['enemy']
        effects = session.get('effects', {'enemy': {}, 'player': {}})
        
        combat_log = f"{character['name']} "
        
        # Специальная обработка для Melee Attack
        if spell_name == "Melee Attack":
            damage = random.randint(1, 6)  # 1d6 урона
            enemy['hp'] -= damage
            combat_log += f"performs melee attack for {damage} damage! "
            
            session['character'] = character
            session['enemy'] = enemy
            return jsonify({
                "combat_log": combat_log,
                "character_hp": character['hp'],
                "enemy_hp": enemy['hp'],
                "enemy_defeated": enemy['hp'] <= 0,
                "spell_slots": character['spell_slots']
            })

        # Определяем уровень заклинания для всех остальных заклинаний
        spell_level = None
        if spell_name in spells_1lvl:
            spell_level = '1'
        elif spell_name in spells_2lvl:
            spell_level = '2'
        
        # Проверяем наличие ячеек нужного уровня
        if spell_level and character['spell_slots'].get(spell_level, 0) <= 0:
            return jsonify({"error": f"No {spell_level}-level spell slots remaining!"})
        
        # Проверяем слоты только для настоящих заклинаний
        if spell_name in basic_attacks:
            is_spell = False
        else:
            is_spell = True
            if character['spell_slots']['1'] <= 0 and character['spell_slots']['2'] <= 0:
                return jsonify({"error": "No spell slots remaining!"})

        # Специальная обработка для каждого заклинания
        if spell_name == "Hold Person":
            effects['enemy']['paralyze'] = {
                'duration': 3,
                'source': spell_name,
                'breaks_on_damage': True  # Новый флаг для эффектов, которые спадают при уроне
            }
            combat_log += "casts Hold Person and paralyzes the enemy! "

        elif spell_name == "Ice Knife":
            damage = random.randint(1, 6)
            enemy['hp'] -= damage
            effects['enemy']['frozen'] = {'duration': 1, 'source': spell_name}
            combat_log += f"hits with Ice Knife for {damage} damage and freezes the enemy! "

        elif spell_name == "Healing Word":
            healing = random.randint(1, 4) + 2
            old_hp = character['hp']
            character['hp'] = min(character['hp'] + healing, character['max_hp'])
            actual_healing = character['hp'] - old_hp
            combat_log += f"uses Healing Word and heals for {actual_healing} HP! "

        elif spell_name == "Chromatic Orb":
            damage = random.randint(1, 8)
            enemy['hp'] -= damage
            effects['enemy']['fear'] = {'duration': 1, 'source': spell_name}
            combat_log += f"hits with Chromatic Orb for {damage} damage and frightens the enemy! "

        elif spell_name == "Magic Missile":
            damage = random.randint(1, 4) + random.randint(1, 4) + random.randint(1, 4)
            enemy['hp'] -= damage
            combat_log += f"launches Magic Missiles for {damage} damage! "

        elif spell_name == "Burning Hands":
            damage = random.randint(1, 6)
            enemy['hp'] -= damage
            effects['enemy']['burning'] = {'duration': 2, 'source': spell_name}
            combat_log += f"burns enemy for {damage} damage and sets them on fire! "

        elif spell_name == "Thunder Wave":
            damage = random.randint(1, 8)
            enemy['hp'] -= damage
            effects['enemy']['stunned'] = {'duration': 1, 'source': spell_name}
            combat_log += f"hits with Thunder Wave for {damage} damage and stuns the enemy! "

        elif spell_name == "Scorching Ray":
            total_damage = 0
            hits = []
            for i in range(3):
                if random.randint(1, 20) >= 10:  # Hit roll for each ray
                    damage = random.randint(1, 6)
                    total_damage += damage
                    hits.append(damage)
            if hits:
                enemy['hp'] -= total_damage
                combat_log += f"hits with Scorching Ray for {total_damage} damage ({', '.join(map(str, hits))})! "
            else:
                combat_log += "misses with all Scorching Rays! "

        elif spell_name == "Dragon's Breath":
            damage = random.randint(1, 10)
            enemy['hp'] -= damage
            effects['enemy']['fear'] = {'duration': 1, 'source': spell_name}
            combat_log += f"breathes fire for {damage} damage and frightens the enemy! "

        elif spell_name == "Cloud of Daggers":
            damage = random.randint(1, 6)
            enemy['hp'] -= damage
            effects['enemy']['bleeding'] = {'duration': 3, 'source': spell_name}
            combat_log += f"creates Cloud of Daggers for {damage} damage and causes bleeding! "

        # Используем слот заклинания соответствующего уровня
        if spell_level:
            character['spell_slots'][spell_level] -= 1
        
        # Сохраняем изменения
        session['character'] = character
        session['enemy'] = enemy
        session['effects'] = effects
        session.modified = True
        
        return jsonify({
            "combat_log": combat_log,
            "character_hp": character['hp'],
            "enemy_hp": enemy['hp'],
            "enemy_defeated": enemy['hp'] <= 0,
            "spell_slots": character['spell_slots']
        })
        
    except Exception as e:
        print(f"Error casting spell: {e}")
        return jsonify({"error": f"Failed to cast spell: {str(e)}"})

if __name__ == "__main__":
    # This web UI runs on port 5000.
    app.run(port=5000, debug=True) 