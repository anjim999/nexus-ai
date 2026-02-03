
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print(f"Testing Gemini 1.5 Flash with API Key: {api_key[:5]}...")

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print("\nSUCCESS!")
    print(response.text)
except Exception as e:
    print("\nFAILURE!")
    print(f"Type: {type(e).__name__}")
    print(f"Error: {e}")
