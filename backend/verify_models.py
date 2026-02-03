
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

with open("available_models.txt", "w", encoding="utf-8") as f:
    f.write("Listing ALL models:\n")
    try:
        for m in genai.list_models():
            f.write(f"Name: {m.name}\n")
            f.write(f"Methods: {m.supported_generation_methods}\n")
            f.write("-" * 20 + "\n")
    except Exception as e:
        f.write(f"Error listing models: {e}\n")
