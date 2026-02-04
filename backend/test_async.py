import asyncio
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

async def main():
    print("Start async test with gemini-2.0-flash")
    # Try gemini-2.0-flash which should be available
    model = genai.GenerativeModel("models/gemini-2.0-flash")
    print("Model initialized")
    try:
        response = await asyncio.to_thread(model.generate_content, "Hello")
        print("Response received")
        print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
