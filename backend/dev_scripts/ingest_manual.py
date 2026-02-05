
import asyncio
import os
import uuid
import sys
from pathlib import Path

# Add backend directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rag.vectorstore import get_vector_store, init_vector_store
from app.config import settings

async def ingest_file(file_path: str):
    """Ingest a single file"""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return

    print(f"📄 Processing: {path.name}...")
    
    vs = get_vector_store()
    
    # Generate a unique ID (or use filename hash if you want idempotency)
    doc_id = str(uuid.uuid4())
    
    try:
        chunks = await vs.add_document(
            file_path=str(path),
            doc_id=doc_id,
            metadata={"source": "manual_ingest"}
        )
        print(f"✅ Successfully ingested {path.name} ({chunks} chunks)")
    except Exception as e:
        print(f"❌ Error ingesting {path.name}: {e}")

async def main():
    # Initialize vector store
    await init_vector_store()
    
    # Files to ingest
    files = [
        "../sample_project_plan.txt",
        "../sample_report.txt"
    ]
    
    print(f"🚀 Starting ingestion of {len(files)} files...")
    
    for file in files:
        # Resolve absolute path
        abs_path = os.path.abspath(os.path.join(os.getcwd(), file))
        await ingest_file(abs_path)
        
    print("✨ Ingestion complete!")

if __name__ == "__main__":
    asyncio.run(main())
