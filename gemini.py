import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

class GeminiChat:
    def __init__(self, system_instruction=None, temperature=0.9):
        # Load environment variables
        load_dotenv()
        
        # Configure the Gemini API
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
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
        
        # Initialize chat session
        self.chat = self._create_chat_session()
    
    def _create_chat_session(self):
        """Create a new chat session with the configured settings."""
        return self.client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=self.temperature,
                safety_settings=self.safety_settings
            )
        )
    
    def send_message(self, message):
        """Send a message to the chat and return the response."""
        try:
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def reset_chat(self):
        """Reset the chat session with the same configuration."""
        self.chat = self._create_chat_session()


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
    
    def send_message_stream(self, prompt):
        """Send a message to the chat and return a streaming response."""
        try:
            return self.client.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=self.temperature,
                    safety_settings=self.safety_settings
                )
            )
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    # Create a chat instance
    chat = GeminiChat()
    load_dotenv()
    gemini = Gemini(os.getenv("GEMINI_API_KEY"))
    
    print("Chat with Gemini 2.0 Flash (Type 'quit' to exit, 'stream' to toggle streaming mode)")
    print("-" * 50)
    
    streaming_mode = False
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'quit':
            print("\nGoodbye!")
            break
            
        if user_input.lower() == 'stream':
            streaming_mode = not streaming_mode
            print(f"\nStreaming mode: {'enabled' if streaming_mode else 'disabled'}")
            continue
        
        if streaming_mode:
            print("\nGemini:", end=" ")
            for chunk in gemini.send_message_stream(user_input):
                print(chunk.text, end="", flush=True)
            print()  # New line after streaming completes
        else:
            response = gemini.send_message(user_input)
            print("\nGemini:", response)

if __name__ == "__main__":
    main()
