from flask import Flask, render_template, request, jsonify, session, Response
from DEF import DnDGame
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    game = DnDGame()
    session['language'] = request.json.get('language', 'en')
    game.language = session['language']
    game.initialize_chat()
    session['game_state'] = {
        'started': True,
        'character_created': False,
        'in_combat': False,
        'player_race': '',
        'player_class': '',
        'health_points': 0,
        'gold': 0,
        'level': 0,
        'damage': 0,
        'magic_1lvl': 0,
        'magic_2lvl': 0
    }
    return jsonify({'status': 'success'})

@app.route('/get_races')
def get_races():
    races = {
        'Human': {'hp': 15, 'damage': '2-7', 'gold': 5},
        'Elf': {'hp': 10, 'damage': '1-12', 'gold': 5},
        'Dwarf': {'hp': 18, 'damage': '1-8', 'gold': 8},
        'Orc': {'hp': 8, 'damage': '3-12', 'gold': 3},
        'Halfling': {'hp': 12, 'damage': '1-6', 'gold': 10},
        'Dragonborn': {'hp': 14, 'damage': '2-8', 'gold': 6},
        'Tiefling': {'hp': 12, 'damage': '1-10', 'gold': 5},
        'Gnome': {'hp': 10, 'damage': '1-6', 'gold': 7}
    }
    return jsonify(races)

@app.route('/get_classes')
def get_classes():
    classes = {
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
    return jsonify(classes)

@app.route('/choose_character', methods=['POST'])
def choose_character():
    data = request.json
    game = DnDGame()
    game.language = session.get('language', 'en')
    game.initialize_chat()  # Initialize chat first
    game.player_race = data['race']
    game.player_class = data['class']
    game.initialize_character()
    
    # Generate opening scene
    opening_scene_response = game.start_game()
    opening_scene_text = opening_scene_response.get('message', 'Welcome to your adventure!')
    
    # Add opening scene to message history
    game.add_to_history("start_game", opening_scene_text)
    
    # Update session state
    session['game_state'] = game.get_state_dict()
    
    return jsonify({
        'status': 'success',
        'stats': session['game_state'],
        'opening_scene': opening_scene_text
    })

@app.route('/game_action', methods=['POST'])
def game_action():
    if 'game_state' not in session:
        return jsonify({'error': 'Game not started'})
        
    try:
        data = request.get_json()
        action = data.get('action')
        
        game = DnDGame()
        game.load_state_from_dict(session['game_state'])
        
        response = game.send_message(action)
        
        # Update session state
        session['game_state'] = game.get_state_dict()
        
        return jsonify({
            'response': response.get('message', ''),
            'stats': session['game_state'],
            'dice_needed': response.get('dice_roll_needed', False),
            'dice_type': response.get('dice_type', None),
            'required_action': response.get('required_action', None),
            'combat_result': response.get('combat_result', None)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/combat_action', methods=['POST'])
def combat_action():
    if 'game_state' not in session:
        return jsonify({'error': 'Game not started'}), 400
        
    data = request.json
    action = data.get('action')
    game = DnDGame()
    game.load_state_from_dict(session['game_state'])
    
    if action == 'start':
        response = game.start_combat()
    else:
        response = game.process_combat_action(action)
    
    session['game_state'] = game.get_state_dict()
    
    return jsonify({
        'response': response,
        'stats': session['game_state'],
        'in_combat': game.in_combat
    })

@app.route('/save_game', methods=['POST'])
def save_game():
    if 'game_state' not in session:
        return jsonify({'error': 'Game not started'}), 400
        
    data = request.json
    save_name = data.get('save_name', 'quicksave')
    game = DnDGame()
    game.load_state_from_dict(session['game_state'])
    response = game.save_game(save_name)
    
    return jsonify({'message': response})

@app.route('/load_game', methods=['POST'])
def load_game():
    data = request.json
    save_name = data.get('save_name', 'quicksave')
    game = DnDGame()
    response = game.load_game(save_name)
    
    if 'successfully' in response.lower():
        session['game_state'] = game.get_state_dict()
        return jsonify({
            'status': 'success',
            'message': response,
            'stats': session['game_state']
        })
    else:
        return jsonify({
            'status': 'error',
            'message': response
        })

@app.route('/list_saves')
def list_saves():
    game = DnDGame()
    saves = game.list_saves()
    return jsonify({'saves': saves})

@app.route('/roll_dice', methods=['POST'])
def roll_dice():
    if 'game_state' not in session:
        return jsonify({'error': 'Game not started'}), 400
    
    game = DnDGame()
    game_state = session['game_state']
    
    # Load the full game state
    game.load_state_from_dict(game_state)
    
    # Get dice type from request or use default
    data = request.get_json()
    dice_type = data.get('dice_type', 'd20')  # Default to d20 if not specified
    
    # Roll the dice
    roll_result = game.roll_dice(dice_type)
    
    if roll_result is None:
        return jsonify({'error': 'Invalid dice type'}), 400
    
    # Send the roll result to get the game's response
    response = game.send_message(f"I rolled {roll_result} on {dice_type}")
    
    # Update session state
    session['game_state'] = game.get_state_dict()
    
    # Format response
    return jsonify({
        'roll': roll_result,
        'dice_type': dice_type,
        'message': response.get('message', ''),
        'stats': session['game_state'],
        'dice_roll_needed': response.get('dice_roll_needed', False),
        'dice_type': response.get('dice_type', dice_type),
        'combat_result': response.get('combat_result'),
        'state_update': response.get('state_update')
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)