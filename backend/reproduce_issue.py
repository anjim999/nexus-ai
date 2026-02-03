
import asyncio
import os
from dotenv import load_dotenv

# Load env vars first so config works
load_dotenv()

# Set up path so we can import app modules
import sys
sys.path.append(os.getcwd())

from app.llm.gemini import GeminiClient

async def reproduce():
    print("Initializing GeminiClient...")
    try:
        client = GeminiClient()
        print(f"Client initialized with model: {client.model.model_name}")
        
        print("Attempting generation...")
        response = await client.generate("Hello, are you working?")
        print(f"Success! Response: {response}")
        
    except Exception as e:
        print("\nCAUGHT EXCEPTION IN MAIN:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
