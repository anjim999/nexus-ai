import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

sys.path.append(os.getcwd())

from app.config import settings
settings.LLM_MODEL = "models/gemini-2.5-flash"

from app.llm.gemini import GeminiClient
from app.agents.specialized.analyst_agent import AnalystAgent

async def test_agent():
    print(f"Initializing Analyst Agent with model: {settings.LLM_MODEL}...")
    try:
        client = GeminiClient()
        agent = AnalystAgent(client)
        
        # Query that should hit the real seeded DB
        query = "What are the top 5 most expensive products?"
        
        print(f"Query: {query}")
        print("Calling agent.analyze()...")
        
        results = await agent.analyze(
            query=query,
            context=[]
        )
        
        print("\n=== Analysis Results ===")
        print(f"Action: {results.get('action')}")
        print(f"SQL Query (Generated): {results.get('sql_query')}")
        print(f"Data Points: {len(results.get('data'))}")
        
        print("\nData Preview:")
        for row in results.get('data', [])[:5]:
            print(row)
            
        print(f"\nSummary: {results.get('summary')}")

    except Exception as e:
        print("\nAGENT TEST FAILED:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
