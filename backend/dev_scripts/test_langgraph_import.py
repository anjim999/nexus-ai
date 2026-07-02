from typing import Dict, TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

# Define state schema
class AgentState(TypedDict):
    query: str
    steps: list

def node_research(state: AgentState):
    print("Research Node Executing...")
    new_steps = list(state.get("steps", []))
    new_steps.append("research")
    return {"steps": new_steps}

def node_reasoning(state: AgentState):
    print("Reasoning Node Executing...")
    new_steps = list(state.get("steps", []))
    new_steps.append("reasoning")
    return {"steps": new_steps}

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("research", node_research)
workflow.add_node("reasoning", node_reasoning)

workflow.set_entry_point("research")
workflow.add_edge("research", "reasoning")
workflow.add_edge("reasoning", END)

app = workflow.compile()

# Run
res = app.invoke({"query": "test query", "steps": []})
print("Result State:", res)
