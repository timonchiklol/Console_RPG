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
    opening_scene = game.start_game()
    
    # Add opening scene to message history
    game.add_to_history("start_game", opening_scene)
    
    session['game_state'] = {
        'started': True,
        'character_created': True,
        'in_combat': False,
        'player_race': game.player_race,
        'player_class': game.player_class,
        'health_points': game.health_points,
        'gold': game.gold,
        'level': game.level,
        'damage': game.damage,
        'magic_1lvl': game.magic_1lvl,
        'magic_2lvl': game.magic_2lvl,
        'enemy': None,
        'language': game.language,
        'message_history': game.message_history  # Use the game's message history with opening scene
    }
    
    return jsonify({
        'status': 'success',
        'stats': session['game_state'],
        'opening_scene': opening_scene
    })

@app.route('/stream_message', methods=['POST'])
def stream_message():
    if 'game_state' not in session:
        return jsonify({'error': 'Game not started'}), 400
        
    data = request.json
    action = data.get('action')
    game = DnDGame()
    
    # Ensure all required fields exist in game state
    game_state = session['game_state'].copy()  # Make a copy of the session state
    if 'enemy' not in game_state:
        game_state['enemy'] = None
    if 'language' not in game_state:
        game_state['language'] = 'en'
    if 'message_history' not in game_state:
        game_state['message_history'] = []
    if 'dice_roll_needed' not in game_state:
        game_state['dice_roll_needed'] = False
    if 'dice_type' not in game_state:
        game_state['dice_type'] = None
    
    game.language = game_state['language']
    game.initialize_chat()
    game.load_state_from_dict(game_state)
    game.message_history = game_state.get('message_history', [])
    game.dice_roll_needed = game_state.get('dice_roll_needed', False)
    game.dice_type = game_state.get('dice_type')
    game.streaming_mode = True  # Ensure streaming is enabled
    
    # Create a response queue to store the complete response
    response_chunks = []
    current_stats = f"""Current player stats:
    Race: {game.player_race}
    Class: {game.player_class}
    Level: {game.level}
    HP: {game.health_points}
    Damage: {game.damage}
    Gold: {game.gold}
    Magic slots (1st/2nd level): {game.magic_1lvl}/{game.magic_2lvl}
    """
    
    # Get limited context from message history
    start_idx = max(0, len(game.message_history) - game.context_limit)
    context = f"Previous messages (last {game.context_limit}):\n"
    for msg in game.message_history[start_idx:]:
        context += f"Player: {msg['user']}\nDM: {msg['dm']}\n"
    
    full_message = f"{current_stats}\n{context}\nCurrent message: {action}"
    
    def generate():
        for chunk in game.chat.send_message_stream(full_message):
            chunk_text = chunk.text
            response_chunks.append(chunk_text)
            yield f"data: {json.dumps({'chunk': chunk_text})}\n\n"
        
        # After all chunks are received, update the game state
        response = "".join(response_chunks)
        game.add_to_history(action, response)
        
        # Update session state
        new_state = game.get_state_dict()
        new_state['message_history'] = game.message_history
        new_state['dice_roll_needed'] = game.dice_roll_needed
        new_state['dice_type'] = game.dice_type
        with app.app_context():
            session['game_state'] = new_state
        
        yield f"data: {json.dumps({'complete': True, 'stats': new_state})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/roll_dice', methods=['POST'])
def roll_dice():
    if 'game_state' not in session:
        return jsonify({'error': 'Game not started'}), 400
    
    game = DnDGame()
    game_state = session['game_state']
    
    # Load the full game state
    game.load_state_from_dict(game_state)
    game.language = game_state.get('language', 'en')
    game.initialize_chat()
    game.message_history = game_state.get('message_history', [])
    
    # Explicitly set dice roll flags from the game state
    game.dice_roll_needed = game_state.get('dice_roll_needed', False)
    game.dice_type = game_state.get('dice_type')
    
    if not game.dice_roll_needed or not game.dice_type:
        print(f"Dice roll rejected - needed: {game.dice_roll_needed}, type: {game.dice_type}")  # Debug log
        return jsonify({'error': 'No dice roll needed'}), 400
    
    current_dice_type = game.dice_type  # Store the current dice type before rolling
    roll_result = game.roll_dice(game.dice_type)
    print(f"🎲 Dice roll: {roll_result} on {current_dice_type}")  # Debug log
    
    if roll_result is None:
        print("Invalid dice roll - returned None")  # Debug log
        return jsonify({'error': 'Invalid dice type'}), 400
    
    # Send the roll result to get the game's response
    response = game.send_message(f"I rolled {roll_result} on {current_dice_type}")
    print(f"Game response after roll: {response}")  # Debug log
    
    # Update session state
    new_state = game.get_state_dict()
    new_state['message_history'] = game.message_history
    session['game_state'] = new_state
    
    # Format the response for the client
    return jsonify({
        'roll': roll_result,
        'dice_type': current_dice_type,
        'message': response.get('message', ''),
        'stats': new_state,
        'required_action': response.get('required_action'),
        'dice_roll_needed': response.get('dice_roll_needed', False),
        'new_dice_type': response.get('dice_type')
    })

@app.route('/game_action', methods=['POST'])
def game_action():
    print("Game action called")  # Debug log
    
    if 'game_state' not in session:
        print("No game state found")  # Debug log
        return jsonify({'error': 'Game not started'})
        
    try:
        data = request.get_json()
        action = data.get('action')
        
        print(f"Processing action: {action}")  # Debug log
        
        game = DnDGame()
        game.load_state_from_dict(session['game_state'])
        
        # Load message history if it exists
        if 'message_history' in session:
            game.message_history = session['message_history']
        
        response = game.send_message(action)
        print(f"Game response: {response}")  # Debug log
        
        # Update both game state and message history in session
        game_state = game.get_state_dict()
        session['game_state'] = game_state
        session['message_history'] = game.message_history
        
        return jsonify({
            'response': response.get('message', ''),
            'stats': game_state,
            'dice_needed': game.dice_roll_needed,
            'dice_type': game.dice_type,
            'state_update': response.get('state_update'),
            'required_action': response.get('required_action'),
            'combat_result': response.get('combat_result')
        })
        
    except Exception as e:
        print(f"Error in game_action: {str(e)}")  # Debug log
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

if __name__ == '__main__':
    app.run(debug=True, port=8000)