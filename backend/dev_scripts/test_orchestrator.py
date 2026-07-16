import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

from dotenv import load_dotenv

# Load env vars
load_dotenv()

sys.path.append(os.getcwd())

from app.config import settings
settings.LLM_MODEL = "models/gemini-2.5-flash"

# Mock chat repo BEFORE importing orchestrator
sys.modules["app.database.repositories.chat"] = MagicMock()
mock_chat_repo = MagicMock()
mock_chat_repo.add_message = AsyncMock()
sys.modules["app.database.repositories.chat"].chat_repo = mock_chat_repo

from app.llm.gemini import GeminiClient
from app.agents.orchestrator import AgentOrchestrator

# Mock Retriever
class MockRetriever:
    async def retrieve(self, query, top_k=5, file_filter=None):
        return [{
            "source": "test_doc.txt", 
            "content": "AI is changing the world.", 
            "score": 0.9,
            "doc_id": "1"
        }]

async def test_agent():
    print(f"Initializing Orchestrator with model: {settings.LLM_MODEL}...")
    try:
        client = GeminiClient()
        
        # Inject mocks
        orchestrator = AgentOrchestrator(llm_client=client)
        orchestrator.retriever = MockRetriever()
        orchestrator.research_agent.retriever = MockRetriever()
        
        # Mocking chat_repo on the instance just in case
        orchestrator.chat_repo = mock_chat_repo
        
        query = "What does the document say about AI?"
        print(f"Query: {query}")
        print("Processing query...")
        
        result = await orchestrator.process_query(query)
        
        print("\n=== Orchestrator Results ===")
        print(f"Response: {result.get('response')}")
        print(f"Confidence: {result.get('confidence')}")
        print("\nAgent Steps:")
        for step in result.get("agent_steps", []):
            print(f"- {step['agent']}: {step['status']}")
            if step['action']:
                print(f"  Action: {step['action']}")

    except Exception as e:
        print("\nORCHESTRATOR TEST FAILED:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
