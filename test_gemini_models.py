import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {api_key[:5]}...")

genai.configure(api_key=api_key)

models = [
    'gemini-1.5-flash',
    'gemini-1.5-flash-latest',
    'gemini-flash-latest', # Current one
    'gemini-pro'
]

for model_name in models:
    print(f"\nTesting model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello")
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Failed: {e}")
