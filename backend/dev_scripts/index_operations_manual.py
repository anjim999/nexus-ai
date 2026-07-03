import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()
sys.path.append(os.getcwd())

from app.rag.vectorstore import get_vector_store

async def main():
    print("Indexing company_operations_manual.txt...")
    store = get_vector_store()
    
    file_path = "test_files/company_operations_manual.txt"
    if not os.path.exists(file_path):
        file_path = "../test_files/company_operations_manual.txt"
        
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    try:
        chunks = await store.add_document(
            file_path=file_path,
            doc_id="company_operations_manual",
            metadata={
                "type": "operations_manual",
                "department": "IT & Sales"
            }
        )
        print(f"Successfully indexed {chunks} chunks.")
        print(f"Current Stats: {store.get_stats()}")
    except Exception as e:
        print(f"Failed to index: {e}")

if __name__ == "__main__":
    asyncio.run(main())
