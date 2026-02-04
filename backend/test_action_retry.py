import asyncio
import os
import sys
import time
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
    from app.core.exceptions import LLMException
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def test_agent():
    print(f"Initializing Action Agent with model: {settings.LLM_MODEL}...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = GeminiClient()
            agent = ActionAgent(client)
            
            query = "Please send an email to the marketing team with the Q3 report attached."
            response = "I have analyzed the Q3 data and the revenue is up by 15%."
            
            print(f"Attempt {attempt+1}: Calling agent.execute()...")
            results = await agent.execute(
                query=query,
                response=response,
                context={}
            )
            
            # Check if we actually got actions or if it fell back
            if results['actions'] or len(results['action_plan'].get('actions', [])) > 0:
                print("Success!")
                print(f"Executed Actions: {results['actions']}")
                print(f"Plan: {results['action_plan']}")
                return
            else:
                print("Agent returned no actions. Checking if it's due to error...")
                # If "no_action_reason" says "Could not determine actions", it likely failed softly
                if results['action_plan'].get('no_action_reason') == "Could not determine actions":
                     print("Soft failure detected (likely LLM error). Retrying if possible...")
                     raise Exception("Soft failure - LLM extraction failed")
                else:
                     print("Agent decided no action was needed.")
                     print(f"Reason: {results['action_plan'].get('no_action_reason')}")
                     return

        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            if "429" in str(e) or "Quota exceeded" in str(e) or "Soft failure" in str(e):
                wait_time = 60
                print(f"Rate limit hit or soft failure. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                import traceback
                traceback.print_exc()
                break
    
    print("Failed after max retries")

if __name__ == "__main__":
    asyncio.run(test_agent())
