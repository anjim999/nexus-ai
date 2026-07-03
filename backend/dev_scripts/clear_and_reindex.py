import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env vars first so config works
load_dotenv()

# Set up path so we can import app modules
sys.path.append(os.getcwd())

from app.rag.vectorstore import get_vector_store
from app.llm.gemini import GeminiClient
from app.agents.orchestrator import AgentOrchestrator

async def run_indexing_and_tests():
    print("=== Step 1: Clearing Vector Store ===")
    store = get_vector_store()
    store.documents = []
    store.metadata = {}
    store._create_index()
    store._save()
    print("Vector store cleared successfully.\n")

    print("=== Step 2: Indexing New Complex Documents ===")
    test_files = [
        ("test_files/company_operations_manual.txt", "ops_manual"),
        ("test_files/customer_feedback_report.txt", "feedback_report"),
        ("test_files/q1_sales_performance.csv", "sales_csv")
    ]

    for file_path, doc_id in test_files:
        if not os.path.exists(file_path):
            # Try parent directory if run from backend/
            alt_path = os.path.join("..", file_path)
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                print(f"Error: {file_path} not found.")
                return
        
        print(f"Indexing {file_path}...")
        chunks = await store.add_document(
            file_path=file_path,
            doc_id=doc_id,
            metadata={"test_run": True}
        )
        print(f"Indexed {chunks} chunks for {doc_id}.")
    
    print("\nVector Store Stats:")
    print(store.get_stats())
    print("\n")

    print("=== Step 3: Initializing Orchestrator & Running Complex Query ===")
    complex_query = (
        "Search our company documents for Acme Corp's rate limit issues. "
        "Also query the sales database to calculate the total sales of 'Product 1'. "
        "My main intent is to calculate total sales, send an email report to anjaneyulumandagiri@gmail.com, "
        "and schedule a daily database backup task at 12:00 PM."
    )
    print(f"Query: {complex_query}\n")

    # Mock chat repo BEFORE importing orchestrator to prevent db connection errors
    from unittest.mock import MagicMock, AsyncMock
    sys.modules["app.database.repositories.chat"] = MagicMock()
    mock_chat_repo = MagicMock()
    mock_chat_repo.add_message = AsyncMock()
    sys.modules["app.database.repositories.chat"].chat_repo = mock_chat_repo

    client = GeminiClient()
    orchestrator = AgentOrchestrator(llm_client=client)
    orchestrator.chat_repo = mock_chat_repo

    print("Executing query through the multi-agent system...")
    result = await orchestrator.process_query(complex_query)

    print("\n=== Execution Summary ===")
    print(f"Response:\n{result.get('response')}\n")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Actions Executed: {result.get('actions_taken')}")
    
    print("\nAgent Steps:")
    for step in result.get("agent_steps", []):
        print(f"- {step['agent']}: {step['status']}")
        if step['action']:
            print(f"  Action: {step['action']}")
        if step.get('duration_ms'):
            print(f"  Duration: {step['duration_ms']}ms")

if __name__ == "__main__":
    asyncio.run(run_indexing_and_tests())
