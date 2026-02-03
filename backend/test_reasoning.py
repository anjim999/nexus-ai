
import asyncio
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

import sys
sys.path.append(os.getcwd())

from app.llm.gemini import GeminiClient
from app.agents.specialized.reasoning_agent import ReasoningAgent

async def test_agent():
    print("Initializing Agent...")
    client = GeminiClient()
    agent = ReasoningAgent(client)
    
    query = "What was the total revenue in Q3 2024 and how much did it grow?"
    documents = [
        {
            "source": "sample_report.txt",
            "content": "TECH CORP Q3 2024 PERFORMANCE REPORT. Total Revenue: $4.2M (+15% YoY). Net Profit: $1.4M (+41% YoY)."
        }
    ]
    
    print("Calling agent.reason()...")
    try:
        results = await agent.reason(
            query=query,
            documents=documents,
            data=[],
            context={}
        )
        print("Success!")
        print(f"Response: {results['response']}")
    except Exception as e:
        print("\nAGENT REASON FAILED:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
