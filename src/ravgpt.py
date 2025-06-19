from openai import OpenAI
import os
from dotenv import load_dotenv

# Initialize environment
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gpt_model="gpt-4.1"

def ravgpt():
    response = client.models.generate_content(
        model=gpt_model, 
        contents="Explain how the Talmud works in a few words"
    )
    return response.text

def ravgpt(msg):
    response = client.models.generate_content(
        model=gpt_model, contents=msg
    )
    return response.text

print(response.output_text)