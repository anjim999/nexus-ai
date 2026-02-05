import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

sys.path.append(os.getcwd())

from app.config import settings
# Ensure we use the user-requested model
settings.LLM_MODEL = "models/gemini-2.5-flash"

try:
    from app.llm.gemini import GeminiClient
    from app.agents.specialized.action_agent import ActionAgent
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def test_agent():
    print(f"Initializing Action Agent with model: {settings.LLM_MODEL}...")
    try:
        client = GeminiClient()
        agent = ActionAgent(client)
        
        query = "Please send an email to the marketing team with the Q3 report attached."
        response = "I have analyzed the Q3 data and the revenue is up by 15%."
        
        print("Calling agent.execute()...")
        results = await agent.execute(
            query=query,
            response=response,
            context={}
        )
        print("Success!")
        print(f"Executed Actions: {results['actions']}")
        # print(f"Results: {results['results']}")
        print(f"Plan: {results['action_plan']}")
        
    except Exception as e:
        print("\nAGENT EXECUTE FAILED:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
