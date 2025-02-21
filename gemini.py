import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from gemini_schema import GAME_RESPONSE_SCHEMA, PLAYER_UPDATE_SCHEMA, DICE_ROLL_REQUEST_SCHEMA
import json
import time
import logging

COMPOSITE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": GAME_RESPONSE_SCHEMA["properties"]["message"],
        "player_update_required": GAME_RESPONSE_SCHEMA["properties"]["player_update_required"],
        "dice_roll_required": GAME_RESPONSE_SCHEMA["properties"]["dice_roll_required"],
        "combat_started": GAME_RESPONSE_SCHEMA["properties"]["combat_started"],
        "players_update": {
            "type": "array",
            "items": PLAYER_UPDATE_SCHEMA
        },
        "dice_roll_request": DICE_ROLL_REQUEST_SCHEMA
    },
    "required": GAME_RESPONSE_SCHEMA["required"]
}

class Gemini:
    def __init__(self, API_KEY=None, system_instruction=None, temperature=1):
        self.logger = logging.getLogger(__name__)
        self.api_keys = self._load_api_keys(API_KEY)
        self.current_key_index = 0
        self.retry_delay = 20  # seconds to wait before retry
        self.max_retries = len(self.api_keys) + 1  # one retry per key + one final retry
        
        # Initialize model and settings
        self.model = "gemini-2.0-flash"
        self.temperature = temperature
        self.system_instruction = system_instruction or "You are a helpful AI assistant."
        
        # Configure safety settings
        self.safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]
        
        self._initialize_client()

    def _load_api_keys(self, provided_key=None):
        """Load API keys from environment variables"""
        keys = []
        if provided_key:
            keys.append(provided_key)
        
        # Load all GEMINI_API_KEY_* variables from .env
        for key, value in os.environ.items():
            if key.startswith('GEMINI_API_KEY') and value not in keys:
                keys.append(value)
        
        if not keys:
            raise ValueError("No Gemini API keys found")
        
        return keys

    def _initialize_client(self):
        """Initialize Gemini client with current API key"""
        self.client = genai.Client(api_key=self.api_keys[self.current_key_index])

    def _rotate_key(self):
        """Rotate to next available API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._initialize_client()
        self.logger.info(f"Rotated to API key {self.current_key_index + 1}/{len(self.api_keys)}")

    def _handle_rate_limit(self, retries):
        """Handle rate limit error by rotating keys or waiting"""
        if retries < len(self.api_keys):
            self._rotate_key()
            return 0  # No need to wait when switching keys
        else:
            self.logger.warning(f"All API keys exhausted. Waiting {self.retry_delay} seconds before retry.")
            return self.retry_delay

    def send_message(self, prompt):
        """Send a message to the chat and return the response."""
        retries = 0
        while retries < self.max_retries:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        temperature=self.temperature,
                        safety_settings=self.safety_settings
                    )
                )
                return response.text
            except Exception as e:
                if "429" in str(e) and retries < self.max_retries - 1:
                    wait_time = self._handle_rate_limit(retries)
                    if wait_time > 0:
                        time.sleep(wait_time)
                    retries += 1
                    continue
                return f"Error: {str(e)}"
    
    def send_structured_message(self, prompt):
        """Send a message and get a structured response using multiple schemas."""
        retries = 0
        while retries < self.max_retries:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        temperature=self.temperature,
                        safety_settings=self.safety_settings,
                        response_mime_type="application/json",
                        response_schema=COMPOSITE_SCHEMA
                    )
                )
                
                if hasattr(response, 'text'):
                    try:
                        return json.loads(response.text)
                    except json.JSONDecodeError:
                        return {
                            "message": response.text,
                            "state_update": None,
                            "combat_result": None,
                            "required_action": None
                        }
                else:
                    # Fallback to normal response
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=self.system_instruction,
                            temperature=self.temperature,
                            safety_settings=self.safety_settings
                        )
                    )
                    return {
                        "message": response.text,
                        "state_update": None,
                        "combat_result": None,
                        "required_action": None
                    }
                    
            except Exception as e:
                if "429" in str(e) and retries < self.max_retries - 1:
                    wait_time = self._handle_rate_limit(retries)
                    if wait_time > 0:
                        time.sleep(wait_time)
                    retries += 1
                    continue
                self.logger.error(f"Error: {str(e)}")
                return {
                    "message": f"Error: {str(e)}",
                    "state_update": None,
                    "combat_result": None,
                    "required_action": None
                }

    def create_chat(self):
        """Create and return a new chat session."""
        return self.client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=self.temperature,
                safety_settings=self.safety_settings
            )
        )

    def send_chat_message(self, chat, message):
        """Send a message in a specific chat session and return the response."""
        try:
            response = chat.send_message(message)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    load_dotenv()
    gemini = Gemini(os.getenv("GEMINI_API_KEY"))
    
    print("Chat with Gemini 2.0 Flash")
    print("Commands:")
    print("- 'quit': Exit")
    print("- 'chat': Toggle chat mode (maintains conversation context)")
    print("- 'reset': Reset chat session (only in chat mode)")
    print("-" * 50)
    
    chat_mode = False
    chat_session = None
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'quit':
            print("\nGoodbye!")
            break
            
        if user_input.lower() == 'chat':
            chat_mode = not chat_mode
            if chat_mode:
                chat_session = gemini.create_chat()
            else:
                chat_session = None
            print(f"\nChat mode: {'enabled' if chat_mode else 'disabled'}")
            continue
            
        if user_input.lower() == 'reset' and chat_mode:
            chat_session = gemini.create_chat()
            print("\nChat session reset!")
            continue
            
        if chat_mode:
            response = gemini.send_chat_message(chat_session, user_input)
            print("\nGemini:", response)
        else:
            response = gemini.send_message(user_input)
            print("\nGemini:", response)

if __name__ == "__main__":
    main()
