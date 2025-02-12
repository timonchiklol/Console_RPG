from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import math
from dnd_spells import spells_1lvl, spells_2lvl  # Add this import at the top

app = Flask(__name__)
app.secret_key = 'secret-key-for-session'

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
    return [(c, r) for (c, r) in neighbors if 0 <= c < 10 and 0 <= r < 8]

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
    
    # Return the path that gets closest to target
    return best_path

# Route for character creation – collects basic DnD-like attributes.
@app.route("/", methods=["GET", "POST"])
def character_creation():
    if request.method == "POST":
        name = request.form.get("name", "Adventurer")
        strength = int(request.form.get("strength", 10))
        dexterity = int(request.form.get("dexterity", 10))
        constitution = int(request.form.get("constitution", 10))
        intelligence = int(request.form.get("intelligence", 10))
        wisdom = int(request.form.get("wisdom", 10))
        charisma = int(request.form.get("charisma", 10))
        # Save character in session
        session['character'] = {
            'name': name,
            'strength': strength,
            'dexterity': dexterity,
            'constitution': constitution,
            'intelligence': intelligence,
            'wisdom': wisdom,
            'charisma': charisma,
            'hp': constitution + 10,  # very basic HP calculation
            'spell_slots': 2,         # basic number of spell slots
            'spells': ['Magic Missile', 'Shield'],
            'speed': 30
        }
        # Create a simple enemy for demonstration with position
        session['enemy'] = {
            'name': 'Goblin',
            'hp': 15,
            'attack': 4,
            'pos': {'col': 5, 'row': 4}
        }
        return redirect(url_for("battle"))
    return render_template("create.html")

# Route for battle – shows the character and enemy status and a hexagonal battle field.
@app.route("/battle", methods=["GET"])
def battle():
    if 'character' not in session:
        return redirect(url_for("character_creation"))
    # Pass both spell lists to the template
    return render_template("battle.html", 
                         character=session['character'], 
                         enemy=session['enemy'],
                         spells_1lvl=spells_1lvl,
                         spells_2lvl=spells_2lvl)

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
    
    hit_roll = request.form.get("hit_roll")
    damage_roll = request.form.get("damage_roll")
    
    if hit_roll is not None and damage_roll is not None:
        hit_roll = int(hit_roll)
        damage_roll = int(damage_roll)
        if hit_roll >= 10:
            enemy['hp'] -= damage_roll
            combat_log = f"You attacked and dealt {damage_roll} damage."
        else:
            combat_log = "Your attack missed!"
    else:
        # fallback auto-roll if manual roll not provided
        roll = random.randint(1, 20)
        if roll >= 10:
            damage = random.randint(1, 6)
            enemy['hp'] -= damage
            combat_log = f"You attacked and dealt {damage} damage."
        else:
            combat_log = "Your attack missed!"
    
    session['character'] = character
    session['enemy'] = enemy
    return jsonify({
        "combat_log": combat_log,
        "character_hp": character['hp'],
        "enemy_hp": enemy['hp'],
        "enemy_defeated": enemy['hp'] <= 0
    })

# API endpoint to cast a spell.
@app.route("/api/cast_spell", methods=["POST"])
def api_cast_spell():
    if 'character' not in session or 'enemy' not in session:
        return jsonify({"error": "No battle in progress."})
    
    try:
        data = request.get_json()
        spell_name = data.get('spell_name')
        spell_data = data.get('spell_data')
        target = data.get('target', {})
        
        character = session['character']
        enemy = session['enemy']
        
        if character['spell_slots'] <= 0:
            return jsonify({"error": "No spell slots remaining!"})
        
        combat_log = f"{character['name']} casts {spell_name}! "
        damage = 0
        
        # Обработка всех заклинаний
        if spell_name == "Chromatic Orb":
            damage = sum(random.randint(1, 8) for _ in range(3))
            combat_log += f"Orb explodes for {damage} damage in 2-tile radius! "
        
        elif spell_name == "Magic Missile":
            for _ in range(3):
                missile_damage = random.randint(1, 3)
                damage += missile_damage
                combat_log += f"Missile hits for {missile_damage} force damage! "
        
        elif spell_name == "Ice Knife":
            primary_damage = random.randint(1, 10)
            area_damage = sum(random.randint(1, 6) for _ in range(2))
            damage = primary_damage + area_damage
            combat_log += f"Ice Knife hits for {primary_damage} + {area_damage} area damage! "
        
        elif spell_name == "Healing Word":
            healing = random.randint(1, 4) + 3
            character['hp'] += healing
            combat_log += f"Heals for {healing} HP! "
        
        elif spell_name == "Thunderwave":
            damage = sum(random.randint(1, 5) for _ in range(2))
            combat_log += f"Thunder damages all enemies for {damage}! "
        
        elif spell_name == "Shield":
            character['damage_reduction'] = 0.5
            character['shield_duration'] = 1
            combat_log += "Magical shield reduces incoming damage by half! "
        
        elif spell_name == "Scorching Ray":
            for i in range(3):
                ray_damage = random.randint(1, 9)
                damage += ray_damage
                combat_log += f"Ray {i+1} hits for {ray_damage} fire damage! "
        
        elif spell_name == "Shatter":
            damage = random.randint(1, 15)
            combat_log += f"Shatter deals {damage} thunder damage! "
        
        elif spell_name == "Dragon's Breath":
            damage = sum(random.randint(1, 7) for _ in range(2))
            enemy['disadvantage'] = True
            combat_log += f"Dragon's Breath deals {damage} damage and applies disadvantage! "
        
        elif spell_name == "Mirror Image":
            character['clone'] = {
                'hp': 5,
                'active': True
            }
            combat_log += "Created a mirror image with 5 HP! "
        
        elif spell_name == "Misty Step":
            character['speed'] = float('inf')
            combat_log += "You can now move anywhere on the map! "
        
        elif spell_name == "Cloud of Daggers":
            damage = sum(random.randint(1, 5) for _ in range(2))
            session['cloud_daggers'] = {
                'pos': target,
                'duration': 3,
                'damage': damage
            }
            combat_log += f"Created a cloud of daggers dealing {damage} damage! "
        
        elif spell_name == "Hold Person":
            enemy['paralyzed'] = True
            combat_log += "Enemy is paralyzed until damaged! "

        # Применяем урон если он есть
        if damage > 0:
            enemy['hp'] -= damage

        # Используем слот заклинания
        character['spell_slots'] -= 1
        
        session['character'] = character
        session['enemy'] = enemy
        
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

# Update enemy_attack endpoint to return position and use d20+d6
@app.route("/api/enemy_attack", methods=["POST"])
def api_enemy_attack():
    if 'character' not in session or 'enemy' not in session:
        return jsonify({"error": "No battle in progress."})
    try:
        player_col = int(request.form.get("player_col"))
        player_row = int(request.form.get("player_row"))
        player_pos = (player_col, player_row)
    except (TypeError, ValueError):
        return jsonify({"error": "Player position not provided."})
    
    character = session['character']
    enemy = session['enemy']
    enemy_pos = enemy.get('pos', {'col': 5, 'row': 4})
    enemy_pos = (enemy_pos['col'], enemy_pos['row'])
    
    # Check if already adjacent to player
    if player_pos in get_neighbors(enemy_pos):
        combat_log = "Goblin is already in attack range. "
        new_enemy_pos = enemy_pos
    else:
        # Try to get closer to player, goblin has 30 speed (6 tiles)
        max_steps = 6  # Goblin can move up to 6 tiles
        path = compute_path(enemy_pos[0], enemy_pos[1], player_pos[0], player_pos[1], max_steps)
        steps = len(path) - 1 if path else 0
        
        # Move along path, but try to maintain 1 tile distance if using ranged attack
        new_enemy_pos = path[steps] if steps > 0 else enemy_pos
        
        # If we would end up more than 1 tile away, try to get as close as possible
        dx = new_enemy_pos[0] - player_pos[0]
        dy = new_enemy_pos[1] - player_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 1.5:  # If more than 1 tile away
            # Try to find a spot adjacent to player
            for neighbor in get_neighbors(player_pos):
                if neighbor != enemy_pos:  # Don't stay in place if we can move
                    new_enemy_pos = neighbor
                    break
        
        enemy['pos'] = {'col': new_enemy_pos[0], 'row': new_enemy_pos[1]}
        combat_log = f"Goblin moved {steps} tile(s) to get closer. "
    
    # Attack if adjacent after moving
    if player_pos in get_neighbors(new_enemy_pos):
        hit_roll = random.randint(1, 20)
        if hit_roll >= 10:
            damage_roll = random.randint(1, 6)
            character['hp'] -= damage_roll
            combat_log += f"Goblin hit with a roll of {hit_roll} and dealt {damage_roll} damage!"
        else:
            combat_log += f"Goblin rolled {hit_roll} and missed!"
    else:
        combat_log += "Goblin is not in attack range."
    
    session['character'] = character
    session['enemy'] = enemy
    return jsonify({
        "combat_log": combat_log,
        "character_hp": character['hp'],
        "enemy_hp": enemy['hp'],
        "character_defeated": character['hp'] <= 0,
        "enemy_pos": enemy['pos']
    })

if __name__ == "__main__":
    # This web UI runs on port 8000.
    app.run(port=9000, debug=True) 