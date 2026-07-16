# Project Rules: LangChain Standardization

All backend AI, agent, and RAG components in this project must be implemented using native LangChain abstractions.

## Guidelines
1. **Tool Calling:** Do not use custom text/JSON parsing for tools or actions. Always define tools using LangChain's `@tool` decorator or by subclassing `BaseTool` from `langchain_core.tools`.
2. **Model Bindings:** Bind tools to LLMs natively using `.bind_tools()`.
3. **Orchestration:** Use LangGraph and native LangChain nodes/chains (like `ToolNode` or LCEL pipelines) rather than custom loop managers.
4. **Prompt Templates:** Utilize LangChain prompt templates (`ChatPromptTemplate`, `PromptTemplate`) instead of direct string interpolation where appropriate.
