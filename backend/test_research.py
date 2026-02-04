import asyncio
import os
import sys
from typing import List, Dict, Optional

from dotenv import load_dotenv

# Load env vars
load_dotenv()

sys.path.append(os.getcwd())

from app.config import settings
# Ensure we use the model that works
settings.LLM_MODEL = "models/gemini-2.5-flash"

from app.llm.gemini import GeminiClient
from app.agents.specialized.research_agent import ResearchAgent

# Mock Retriever for testing
class MockRetriever:
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        file_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        print(f"[MockRetriever] Searching for: {query}")
        return [
            {
                "source": "financial_report_2023.pdf",
                "content": "The total revenue for 2023 was $50 million, a 20% increase from 2022.",
                "score": 0.92,
                "page": 5,
                "doc_id": "doc_1"
            },
             {
                "source": "financial_report_2023.pdf",
                "content": "Operating expenses were reduced by 15% due to automation.",
                "score": 0.88,
                "page": 8,
                "doc_id": "doc_2"
            }
        ]

async def test_agent():
    print(f"Initializing Research Agent with model: {settings.LLM_MODEL}...")
    try:
        client = GeminiClient()
        retriever = MockRetriever()
        agent = ResearchAgent(client, retriever)
        
        query = "What was the revenue in 2023?"
        
        print(f"Query: {query}")
        print("Calling agent.search()...")
        
        results = await agent.search(
            query=query,
            top_k=2
        )
        
        print("\n=== Search Results ===")
        print(f"Summary: {results.get('summary')}")
        print(f"Confidence: {results.get('confidence')}")
        print(f"Sources: {len(results.get('sources'))}")
        
        print("\nCalling agent.extract_facts()...")
        facts = await agent.extract_facts(query, results['documents'])
        print(f"Extracted Facts: {facts}")

    except Exception as e:
        print("\nAGENT TEST FAILED:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
