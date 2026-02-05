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
from app.agents.specialized.scheduler_agent import SchedulerAgent

async def test_agent():
    print(f"Initializing Scheduler Agent with model: {settings.LLM_MODEL}...")
    try:
        client = GeminiClient()
        agent = SchedulerAgent(client)
        
        query = "Schedule a weekly sales report generation every Monday at 9 AM"
        
        print(f"Query: {query}")
        print("Calling agent.schedule()...")
        
        results = await agent.schedule(
            query=query,
            context={}
        )
        
        print("\n=== Scheduler Results ===")
        print(f"Status: {results.get('status')}")
        print(f"Message: {results.get('message')}")
        
        details = results.get('job_details', {})
        print("\nJob Details:")
        print(f"- Task: {details.get('task_name')}")
        print(f"- Type: {details.get('schedule_type')}")
        print(f"- Cron: {details.get('cron_expression')}")
        print(f"- Priority: {details.get('priority')}")

    except Exception as e:
        print("\nSCHEDULER TEST FAILED:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
