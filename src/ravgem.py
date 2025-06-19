import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


# Initialize clients
load_dotenv()
client = genai.Client(api_key=os.getenv('gemini_key'))
gemini_model = "gemini-2.5-flash"

def ravgem():
    response = client.models.generate_content(
        model=gemini_model, contents="Explain how the Talmud works in a few words"
    )
    return response.text

def ravgem(msg):
    response = client.models.generate_content(
        model=gemini_model, contents=msg
    )
    return response.text

def ravgem_chat(prev):
    chat = client.chats.create(model=gemini_model) # Create a chat client for the 
    response = chat.send_message(
        prev+ ". What does this mean to you?"
        # Turn off thinking:
        # thinking_config=types.ThinkingConfig(thinking_budget=0)
        # Turn on dynamic thinking:
        # thinking_config=types.ThinkingConfig(thinking_budget=-1)
    )
    return response.text