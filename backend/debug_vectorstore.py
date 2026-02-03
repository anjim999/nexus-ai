
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add backend to path
sys.path.append(os.getcwd())

from app.rag.vectorstore import VectorStore
from app.config import settings

async def inspect_store():
    print("Inspecting Vector Store...")
    print(f"Path: {settings.VECTOR_STORE_PATH}")
    
    vs = VectorStore()
    
    print(f"Total Documents in Metadata: {len(vs.metadata)}")
    print(f"Total Chunks in Memory: {len(vs.documents)}")
    
    if vs.index:
        print(f"FAISS Index Size: {vs.index.ntotal}")
    else:
        print("FAISS Index is None")
        
    print("\n--- Listing Documents ---")
    for doc_id, meta in vs.metadata.items():
        print(f"ID: {doc_id}")
        print(f"File: {meta.get('filename')}")
        print(f"Chunks: {meta.get('chunk_count')}")
        print("-" * 20)

    # Test Search
    query = "What was the total revenue in Q3 2024 and how much did it grow?"
    print(f"\n--- Testing Search: '{query}' ---")
    results = await vs.search(query)
    print(f"Found {len(results)} results")
    for r in results:
        print(f"Score: {r['score']}")
        print(f"Content: {r['content'][:50]}...")

if __name__ == "__main__":
    asyncio.run(inspect_store())
