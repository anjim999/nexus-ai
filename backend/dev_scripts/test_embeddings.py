
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print(f"Testing Embeddings with API Key: {api_key[:5]}...")

models_to_test = ["models/embedding-001", "models/text-embedding-004", "models/gemini-embedding-001"]

for model_name in models_to_test:
    print(f"\nTesting {model_name}...")
    try:
        result = genai.embed_content(
            model=model_name,
            content="This is a test document.",
            task_type="retrieval_document"
        )
        embedding = result['embedding']
        print(f"SUCCESS! Vector length: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"FAILURE: {e}")
