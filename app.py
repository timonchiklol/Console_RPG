from flask import Flask, render_template, request, jsonify, session, Response
from DEF import DnDGame
from character_config import RACE_STATS, CLASS_BONUSES, RACE_TRANSLATIONS, CLASS_TRANSLATIONS
from room_manager import RoomManager
import os
import json
import uuid
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

# Create a custom filter to exclude get_room_state messages
class GetRoomStateFilter(logging.Filter):
    def filter(self, record):
        return "GET /get_room_state" not in record.getMessage()

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler with daily rotation
    log_file = logs_dir / "game.log"
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30  # Keep 30 days of logs
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    file_handler.addFilter(GetRoomStateFilter())
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(detailed_formatter)
    console_handler.addFilter(GetRoomStateFilter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    root_logger.handlers = []
    
    # Add the handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup message
    root_logger.info("Game server starting up...")

# Set up logging before creating the app
setup_logging()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
room_manager = RoomManager()

# Store messages for each room
room_messages = {}

@app.route('/')
def index():
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    language = request.json.get('language', 'en')
    session['language'] = language
    return jsonify({'status': 'success'})

@app.route('/create_room', methods=['POST'])
def create_room():
    if 'player_id' not in session:
        session['player_id'] = str(uuid.uuid4())
    
    player_id = session['player_id']
    player_name = request.json.get('player_name', f'Player_{player_id[:6]}')
    language = session.get('language', 'en')
    
    room_id = room_manager.create_room(player_id, language)
    room = room_manager.join_room(room_id, player_id, player_name)
    
    # Initialize room messages
    room_messages[room_id] = []
    
    session['room_id'] = room_id
    return jsonify({
        'status': 'success',
        'room_id': room_id,
        'player_id': player_id,
        'is_host': True
    })

@app.route('/join_room', methods=['POST'])
def join_room():
    # Always generate new session ID for joining players
    session.clear()
    session['player_id'] = str(uuid.uuid4())  # Generate new unique ID
    
    player_id = session['player_id']
    room_id = request.json.get('room_id')
    player_name = request.json.get('player_name', f'Player_{player_id[:6]}')
    
    logging.info(f"Join room request - Room: {room_id}, Player: {player_name} ({player_id})")
    
    # Get room first to check if it exists
    room = room_manager.get_room(room_id)
    if not room:
        logging.error(f"Room {room_id} not found")
        return jsonify({
            'status': 'error',
            'message': 'Room not found'
        }), 404
    
    # Check if player is already in the room
    if player_id in room.players:
        logging.info(f"Player {player_name} ({player_id}) is already in room {room_id}")
        session['room_id'] = room_id
        session['language'] = room.language
    else:
        # Join room with new player
        room = room_manager.join_room(room_id, player_id, player_name)
        if not room:
            logging.error(f"Failed to join room {room_id}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to join room'
            }), 400
        
        session['room_id'] = room_id
        session['language'] = room.language
        
        # Add system message about player joining
        add_room_message(room_id, f"{player_name} joined the room", 'system')
    
    # Get all existing messages for the new player
    existing_messages = room_messages.get(room_id, [])
    
    # Convert player states to dict with proper translation
    players_dict = {}
    for pid, p in room.players.items():
        player_data = p.model_dump()
        if p.race and p.class_name:
            # Translate race and class names if they exist
            player_data['race'] = RACE_TRANSLATIONS[room.language].get(p.race, p.race)
            player_data['class_name'] = CLASS_TRANSLATIONS[room.language].get(p.class_name, p.class_name)
        players_dict[pid] = player_data
    
    response_data = {
        'status': 'success',
        'room_id': room_id,
        'host_id': room.host_id,
        'player_id': player_id,
        'is_host': room.host_id == player_id,
        'players': players_dict,
        'messages': existing_messages
    }
    
    logging.info(f"Join room response - Room: {room_id}, Host: {room.host_id}, Players: {list(players_dict.keys())}")
    
    return jsonify(response_data)

@app.route('/leave_room', methods=['POST'])
def leave_room():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room_id = session['room_id']
    player_id = session['player_id']
    room = room_manager.get_room(room_id)
    
    if room and player_id in room.players:
        player_name = room.players[player_id].name
        success = room_manager.leave_room(room_id, player_id)
        if success:
            add_room_message(room_id, f"{player_name} left the room", 'system')
            session.pop('room_id', None)
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Failed to leave room'}), 400

@app.route('/get_room_state', methods=['GET'])
def get_room_state():
    if 'room_id' not in session:
        logging.error("Session missing room_id")
        return jsonify({'status': 'error', 'message': 'Not in a room'}), 400
    
    room = room_manager.get_room(session['room_id'])
    if not room:
        logging.error(f"Room {session['room_id']} not found")
        return jsonify({'status': 'error', 'message': 'Room not found'}), 404
    
    # Get messages since last_message_id if provided
    last_message_id = request.args.get('last_message_id')
    messages = []
    
    if session['room_id'] in room_messages:
        if last_message_id is None:
            # First time getting messages, only get the last few
            messages = room_messages[session['room_id']][-5:]
        else:
            # Get only new messages since last_message_id
            try:
                last_id = int(last_message_id)
                messages = [msg for msg in room_messages[session['room_id']] 
                          if msg.get('id', 0) > last_id]
            except ValueError:
                logging.error(f"Invalid last_message_id: {last_message_id}")
                messages = room_messages[session['room_id']][-5:]
    
    # Convert player states to dict with proper translation
    players_dict = {}
    for pid, p in room.players.items():
        player_data = p.model_dump()  # Use model_dump instead of dict
        if p.race and p.class_name:
            # Translate race and class names if they exist
            player_data['race'] = RACE_TRANSLATIONS[room.language].get(p.race, p.race)
            player_data['class_name'] = CLASS_TRANSLATIONS[room.language].get(p.class_name, p.class_name)
        players_dict[pid] = player_data
    
    # Convert room state with translated player data
    room_data = room.model_dump()  # Use model_dump instead of dict
    room_data['players'] = players_dict
    
    response_data = {
        'status': 'success',
        'room': room_data,
        'is_host': room.host_id == session.get('player_id'),
        'messages': messages,
        'last_message_id': messages[-1].get('id') if messages else None
    }
    
    logging.debug(f"Room state response - Players: {list(players_dict.keys())}")
    
    return jsonify(response_data)

@app.route('/get_races')
def get_races():
    language = session.get('language', 'en')
    races = {}
    translations = RACE_TRANSLATIONS[language]
    
    for eng_name, stats in RACE_STATS.items():
        local_name = translations[eng_name]
        races[local_name] = stats
    
    return jsonify(races)

@app.route('/get_classes')
def get_classes():
    language = session.get('language', 'en')
    classes = {}
    translations = CLASS_TRANSLATIONS[language]
    
    for eng_name, stats in CLASS_BONUSES.items():
        local_name = translations[eng_name]
        classes[local_name] = stats
    
    return jsonify(classes)

@app.route('/choose_character', methods=['POST'])
def choose_character():
    if 'room_id' not in session or 'player_id' not in session:
        logging.error("Session missing room_id or player_id")
        return jsonify({'error': 'Not in a room'}), 400
    
    data = request.json
    player_id = session['player_id']
    room_id = session['room_id']
    
    logging.info(f"Received character creation request - Room: {room_id}, Player: {player_id}, Data: {data}")
    
    room = room_manager.get_room(room_id)
    if not room:
        logging.error(f"Room {room_id} not found")
        return jsonify({'error': 'Room not found'}), 404
    
    player = room.players.get(player_id)
    if not player:
        logging.error(f"Player {player_id} not found in room {room_id}")
        return jsonify({'error': 'Player not found'}), 404
    
    # Check if player already has a character
    if player.race and player.class_name:
        logging.error(f"Player {player.name} ({player_id}) already has a character")
        return jsonify({
            'status': 'error',
            'error': 'Character already created'
        }), 400
    
    try:
        # Convert translated names back to English
        language = room.language
        race_translations = RACE_TRANSLATIONS[language]
        class_translations = CLASS_TRANSLATIONS[language]
        
        logging.info(f"Converting from {language}. Race: {data['race']}, Class: {data['class']}")
        
        # Find English names by matching translated names
        selected_race = None
        selected_class = None
        
        for eng_name, translated_name in race_translations.items():
            if translated_name == data['race']:
                selected_race = eng_name
                break
        
        for eng_name, translated_name in class_translations.items():
            if translated_name == data['class']:
                selected_class = eng_name
                break
        
        if not selected_race or not selected_class:
            logging.error(f"Invalid race/class selection. Race: {data['race']}, Class: {data['class']}")
            return jsonify({
                'status': 'error',
                'error': 'Invalid race or class selection'
            }), 400
        
        logging.info(f"Converted names - Race: {selected_race}, Class: {selected_class}")
        
        # Initialize character with English names
        game = DnDGame(language=room.language)
        game.player_race = selected_race
        game.player_class = selected_class
        game.initialize_character()
        
        # Store English names in player state
        player.race = selected_race
        player.class_name = selected_class
        player.health_points = game.health_points
        player.gold = game.gold
        player.damage = game.damage
        player.level = game.level
        player.magic_1lvl = game.magic_1lvl
        player.magic_2lvl = game.magic_2lvl
        
        room_manager.update_room(room)
        
        # Use translated names in the message
        add_room_message(
            room_id,
            f"{player.name} created a {data['race']} {data['class']}",
            'system'
        )
        
        # Get or generate opening scene
        opening_scene_text = None
        room_messages_list = room_messages.get(room_id, [])
        for msg in room_messages_list:
            if msg['type'] == 'dm' and 'tavern' in msg['message'].lower():
                opening_scene_text = msg['message']
                break
        
        # Generate opening scene only if this is the host and no opening scene exists
        if not opening_scene_text and player_id == room.host_id:
            opening_scene_response = game.start_game()
            opening_scene_text = opening_scene_response.get('message', 'Welcome to your adventure!')
            add_room_message(room_id, opening_scene_text, 'dm')
        elif not opening_scene_text:
            opening_scene_text = 'Welcome to your adventure!'
        
        logging.info(f"Character created successfully - Player: {player.name} ({player_id})")
        
        return jsonify({
            'status': 'success',
            'player': player.model_dump(),
            'opening_scene': opening_scene_text
        })
    except Exception as e:
        logging.error(f"Error in choose_character: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 400

@app.route('/game_action', methods=['POST'])
def game_action():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room = room_manager.get_room(session['room_id'])
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    player = room.players.get(session['player_id'])
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    try:
        data = request.get_json()
        action = data.get('action')
        
        game = DnDGame(language=room.language)  # Use room's language
        # Set game state from player state
        game.player_race = player.race
        game.player_class = player.class_name
        game.health_points = player.health_points
        game.gold = player.gold
        game.damage = player.damage
        game.level = player.level
        game.magic_1lvl = player.magic_1lvl
        game.magic_2lvl = player.magic_2lvl
        game.in_combat = room.in_combat
        if room.in_combat:
            game.enemy = {"name": room.enemy_name, "hp": room.enemy_health} if room.enemy_name else None
        
        response = game.send_message(action)
        
        # Add player's action to room messages
        add_room_message(session['room_id'], action, 'player', player.name)
        if response.get('message'):
            add_room_message(session['room_id'], response['message'], 'dm')
        
        # Update player state
        player.health_points = game.health_points
        player.gold = game.gold
        player.damage = game.damage
        player.level = game.level
        player.magic_1lvl = game.magic_1lvl
        player.magic_2lvl = game.magic_2lvl
        
        # Update room state
        room.in_combat = game.in_combat
        if game.enemy:
            room.enemy_name = game.enemy["name"]
            room.enemy_health = game.enemy["hp"]
        else:
            room.enemy_name = None
            room.enemy_health = None
        
        room_manager.update_room(room)
        
        return jsonify({
            'response': response.get('message', ''),
            'player': player.dict(),
            'room': room.dict(),
            'dice_needed': response.get('dice_roll_needed', False),
            'dice_type': response.get('dice_type', None),
            'required_action': response.get('required_action', None),
            'combat_result': response.get('combat_result', None)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/roll_dice', methods=['POST'])
def roll_dice():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room = room_manager.get_room(session['room_id'])
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    player = room.players.get(session['player_id'])
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    game = DnDGame(language=room.language)
    
    data = request.get_json()
    dice_type = data.get('dice_type', 'd20')
    
    roll_result = game.roll_dice(dice_type)
    
    if roll_result is None:
        return jsonify({'error': 'Invalid dice type'}), 400
    
    # Add dice roll to room messages
    add_room_message(
        session['room_id'],
        f"rolled {roll_result} on {dice_type}",
        'player',
        player.name
    )
    
    # Update player's last roll
    player.last_dice_roll = roll_result
    room_manager.update_room(room)
    
    return jsonify({
        'roll': roll_result,
        'dice_type': dice_type,
        'player': player.dict()
    })

@app.route('/process_roll', methods=['POST'])
def process_roll():
    if 'room_id' not in session or 'player_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    room = room_manager.get_room(session['room_id'])
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    player = room.players.get(session['player_id'])
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    data = request.get_json()
    roll_value = data.get('roll')
    dice_type = data.get('dice_type')
    
    game = DnDGame(language=room.language)
    # Set game state from player state
    game.player_race = player.race
    game.player_class = player.class_name
    game.health_points = player.health_points
    game.gold = player.gold
    game.damage = player.damage
    game.level = player.level
    game.magic_1lvl = player.magic_1lvl
    game.magic_2lvl = player.magic_2lvl
    game.in_combat = room.in_combat
    if room.in_combat:
        game.enemy = {"name": room.enemy_name, "hp": room.enemy_health} if room.enemy_name else None
    
    response = game.send_message(f"I rolled {roll_value} on {dice_type}")
    
    if response.get('message'):
        add_room_message(session['room_id'], response['message'], 'dm')
    
    # Update player state
    player.health_points = game.health_points
    player.gold = game.gold
    player.damage = game.damage
    player.level = game.level
    player.magic_1lvl = game.magic_1lvl
    player.magic_2lvl = game.magic_2lvl
    player.last_dice_roll = None  # Reset last roll
    
    # Update room state
    room.in_combat = game.in_combat
    if game.enemy:
        room.enemy_name = game.enemy["name"]
        room.enemy_health = game.enemy["hp"]
    else:
        room.enemy_name = None
        room.enemy_health = None
    
    room_manager.update_room(room)
    
    return jsonify({
        'message': response.get('message', ''),
        'player': player.dict(),
        'room': room.dict(),
        'dice_roll_needed': response.get('dice_roll_needed', False),
        'dice_type': response.get('dice_type', dice_type),
        'combat_result': response.get('combat_result'),
        'state_update': response.get('state_update')
    })

@app.route('/save_game', methods=['POST'])
def save_game():
    if 'room_id' not in session:
        return jsonify({'error': 'Not in a room'}), 400
    
    success = room_manager.save_room(session['room_id'])
    message = 'Game saved successfully' if success else 'Failed to save game'
    if success:
        add_room_message(session['room_id'], message, 'system')
    return jsonify({'message': message})

@app.route('/load_game', methods=['POST'])
def load_game():
    data = request.json
    room_id = data.get('room_id', session.get('room_id'))
    
    if not room_id:
        return jsonify({'error': 'No room ID provided'}), 400
    
    room = room_manager.load_room(room_id)
    if not room:
        return jsonify({'error': 'Failed to load game'}), 400
    
    session['room_id'] = room_id
    add_room_message(room_id, 'Game loaded successfully', 'system')
    
    return jsonify({
        'status': 'success',
        'message': 'Game loaded successfully',
        'room': room.dict()
    })

@app.route('/list_saves')
def list_saves():
    saves = [f.stem.replace('room_', '') for f in Path('saves').glob('room_*.json')]
    return jsonify({'saves': '\n'.join(saves)})

def add_room_message(room_id: str, message: str, message_type: str = 'system', player_name: str = None):
    """Add a message to the room's message history with an ID"""
    if room_id not in room_messages:
        room_messages[room_id] = []
    
    # Get the next message ID
    next_id = len(room_messages[room_id]) + 1
    
    message_data = {
        'id': next_id,
        'message': message,
        'type': message_type,
        'timestamp': datetime.now().isoformat()
    }
    
    # Add player name if provided and message type is 'player'
    if message_type == 'player' and player_name:
        message_data['player_name'] = player_name
    
    room_messages[room_id].append(message_data)
    
    # Keep only the last 100 messages
    if len(room_messages[room_id]) > 100:
        room_messages[room_id] = room_messages[room_id][-100:]

def get_new_messages(room_id: str, last_message_id: str = None):
    """Get messages newer than last_message_id"""
    if room_id not in room_messages:
        return []
    
    if last_message_id is None:
        return room_messages[room_id][-50:]  # Return last 50 messages
    
    try:
        last_id = int(last_message_id)
        return [msg for msg in room_messages[room_id] if msg['id'] > last_id]
    except (ValueError, TypeError):
        return room_messages[room_id][-50:]

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)