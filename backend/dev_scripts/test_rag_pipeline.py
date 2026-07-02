import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()
sys.path.append(os.getcwd())

from app.rag.vectorstore import get_vector_store
from app.rag.embeddings import get_embedding

async def main():
    print("Testing RAG Pipeline with models/gemini-embedding-001...")
    
    # Check embedding function first
    try:
        vec = await get_embedding("Hello world")
        print(f"Embedding success! Vector size: {len(vec)}")
    except Exception as e:
        print(f"Embedding check failed: {e}")
        return

    # Initialize VectorStore
    store = get_vector_store()
    print("VectorStore initialized.")
    
    test_file = "test_files/customer_feedback_report.txt"
    if not os.path.exists(test_file):
        test_file = "../test_files/customer_feedback_report.txt"
    if not os.path.exists(test_file):
        print(f"Test file not found at: {test_file}")
        return
        
    print(f"Indexing file: {test_file}...")
    try:
        chunks_indexed = await store.add_document(
            file_path=test_file,
            doc_id="customer_feedback_test",
            metadata={"test": True}
        )
        print(f"Successfully indexed {chunks_indexed} chunks.")
    except Exception as e:
        print(f"Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\nTesting retrieval / search...")
    try:
        results = await store.search(
            query="Initech Bug response time",
            top_k=2
        )
        print(f"Found {len(results)} results:")
        for idx, res in enumerate(results, 1):
            print(f"\nResult {idx} (Score: {res['score']:.4f}, Source: {res['source']}):")
            print(res['content'])
    except Exception as e:
        print(f"Search failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
