
import asyncio
import sys
import os

# Add backend directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rag.vectorstore import get_vector_store, init_vector_store

async def main():
    print("🔍 initializing vector store...")
    await init_vector_store()
    vs = get_vector_store()
    
    query = "Green Earth Initiative budget"
    print(f"❓ Searching for: '{query}'")
    
    results = await vs.search(query, top_k=10, threshold=0.0)
    
    print(f"found {len(results)} results:")
    for res in results:
        print(f"--- Score: {res['score']} | Source: {res['source']} ---")
        print(res['content'][:200] + "...")
        print("---------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
