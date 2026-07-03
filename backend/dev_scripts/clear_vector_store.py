import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()
sys.path.append(os.getcwd())

from app.rag.vectorstore import get_vector_store

async def main():
    print("Clearing VectorStore documents...")
    store = get_vector_store()
    
    # Reset internal storage
    store.documents = []
    store.metadata = {}
    store._create_index()  # Rebuild blank index
    store._save()
    
    print("VectorStore successfully cleared.")
    print(f"Stats: {store.get_stats()}")

if __name__ == "__main__":
    asyncio.run(main())
