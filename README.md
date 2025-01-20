# D&D Console Adventure - Web Interface

A web-based interface for the D&D Console Adventure game, featuring a modern UI with medieval styling.

## Features

- Beautiful medieval-themed UI with responsive design
- Character creation with race and class selection
- Real-time game state updates
- Combat system
- Save/Load game functionality
- Bilingual support (English/Russian)
- Message history with scrolling
- Character stats display

## Setup

1. Make sure you have Python 3.8+ and uv installed
2. Install the required dependencies:
   ```bash
   uv init
   ```
3. Make sure you have a `.env` file with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Running the Game

1. Start the Flask server:
   ```bash
   uv run app.py
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## How to Play

1. Choose your preferred language (English or Russian)
2. Create your character by selecting a race and class
3. Begin your adventure!

### Available Commands
- `fight`: Start combat with a random enemy
- `save`: Save your current game progress
- `load`: Load a previously saved game
- `style`: Toggle message style
- `quit`: Exit the game

## Game Controls

- Use the action input field to enter custom commands
- Click the "Fight" button to initiate combat
- Save/Load your game progress using the respective buttons
- View your character stats in real-time
- Track your adventure in the message history box

## Technical Details

- Built with Flask (Python web framework)
- Frontend using Vue.js and Tailwind CSS
- Medieval-themed UI with MedievalSharp font
- Responsive design for all screen sizes
- Real-time game state management
- Session-based game progress tracking