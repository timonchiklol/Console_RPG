from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import math

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
    return render_template("battle.html", character=session['character'], enemy=session['enemy'])

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
    character = session['character']
    enemy = session['enemy']
    spell = request.form.get("spell")
    if spell not in character['spells']:
        return jsonify({"error": "Invalid spell."})
    if character['spell_slots'] <= 0:
        return jsonify({"error": "No spell slots left."})
    combat_log = f"{character['name']} casts {spell}. "
    if spell == "Magic Missile":
        damage = random.randint(3, 8)
        enemy['hp'] -= damage
        combat_log += f"Magic Missile deals {damage} damage."
    elif spell == "Shield":
        combat_log += "Shield activated! (But its effect isn't implemented in this demo.)"
    character['spell_slots'] -= 1

    enemy_defeated = enemy['hp'] <= 0
    session['character'] = character
    session['enemy'] = enemy
    return jsonify({
        "combat_log": combat_log,
        "character_hp": character['hp'],
        "enemy_hp": enemy['hp'],
        "enemy_defeated": enemy_defeated
    })

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