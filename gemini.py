import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from gemini_schema import GAME_RESPONSE_SCHEMA
import json


class Gemini:
    def __init__(self, API_KEY, system_instruction=None, temperature=1):
        self.client = genai.Client(api_key=API_KEY)

        # Initialize model and settings
        self.model = "gemini-2.0-flash-exp"
        self.temperature = temperature
        self.system_instruction = system_instruction or "You are a helpful AI assistant."

        # Configure safety settings
        self.safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]


    def send_message(self, prompt):
        """Send a message to the chat and return the response."""
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
            return f"Error: {str(e)}"
    
    def send_structured_message(self, prompt):
        """Send a message and get a structured response using the game response schema."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=self.temperature,
                    safety_settings=self.safety_settings,
                    response_mime_type="application/json",
                    response_schema=GAME_RESPONSE_SCHEMA
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
            print(f"Error: {str(e)}")
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
