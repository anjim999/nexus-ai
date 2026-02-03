
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
print(f"Generative AI Library Version: {genai.__version__}")

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("\nListing available models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTesting Generation with 'gemini-1.5-flash':")
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Say hello")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"gemini-1.5-flash failed: {e}")
    print("\nTesting Generation with 'gemini-pro':")
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content("Say hello")
        print(f"Success! Response: {response.text}")
    except Exception as e2:
        print(f"gemini-pro failed: {e2}")
