
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

with open("result.txt", "w", encoding="utf-8") as f:
    f.write(f"Testing Gemini 1.5 Flash...\n")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        f.write("SUCCESS!\n")
        f.write(response.text)
    except Exception as e:
        f.write("FAILURE!\n")
        f.write(f"Error: {e}\n")
