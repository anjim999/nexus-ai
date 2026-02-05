
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

try:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="Testing connection",
        task_type="retrieval_document"
    )
    print(f"SUCCESS: Vector length {len(result['embedding'])}")
except Exception as e:
    print(f"FAILURE: {e}")
