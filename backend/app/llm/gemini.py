# Gemini LLM Client
# Integration with Google's Gemini API using LangChain

from typing import Optional, List, Dict, Any, AsyncGenerator
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.config import settings
from app.core.exceptions import LLMException


class GeminiClient:
    # Client for Google Gemini API backed by LangChain
    # Features: Text generation, Structured output, Streaming, Chat sessions
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        
        if not self.api_key:
            raise LLMException("GEMINI_API_KEY is required")
        
        # Initialize LangChain ChatGoogleGenerativeAI client
        try:
            self.chat_model = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL, # "models/gemini-2.5-flash"
                google_api_key=self.api_key,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
                top_p=0.95,
                top_k=40
            )
        except Exception as e:
            raise LLMException(f"Failed to initialize LangChain Gemini: {str(e)}")
        
        # Chat session storage (holds lists of LangChain BaseMessages)
        self._chat_sessions: Dict[str, List[Any]] = {}
    
    # Basic Generation using LangChain PromptTemplate & Chain
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        # Pacing sleep to avoid 429 rate limit exceptions on free tier API
        await asyncio.sleep(3.5)
        print(f"--- LangChain Gemini Generating with model: {settings.LLM_MODEL} ---")
        try:
            # Build Chat Prompt Template
            if system_prompt:
                prompt_template = ChatPromptTemplate.from_messages([
                    SystemMessage(content=system_prompt),
                    ("human", "{input}")
                ])
            else:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("human", "{input}")
                ])
                
            # Create LangChain Chain
            chain = prompt_template | self.chat_model | StrOutputParser()
            
            # Execute Chain
            response_text = await chain.ainvoke({"input": prompt})
            return response_text
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            with open("last_gemini_error.txt", "w", encoding="utf-8") as f:
                f.write(error_msg)
            
            print(f"\n\n🚨 ============= LANGCHAIN GEMINI ERROR START ============= 🚨")
            print(f"Model used: {settings.LLM_MODEL}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            print(error_msg)
            print(f"🚨 ================= LANGCHAIN GEMINI ERROR END ================= 🚨\n\n")
            
            raise LLMException(f"Generation failed: {str(e)}")
    
    # Structured Output using LangChain
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def generate_json(
        self,
        prompt: str,
        schema: Any,
        system_prompt: Optional[str] = None
    ) -> Any:
        # Pacing sleep to avoid 429 rate limit exceptions on free tier API
        await asyncio.sleep(3.5)
        # Try native LangChain structured output first
        try:
            from pydantic import BaseModel as BaseModelV2
            from pydantic.v1 import BaseModel as BaseModelV1
            from typing import Type
            
            # Check if schema is already a Pydantic model (either v1 or v2)
            is_pydantic_model = False
            if isinstance(schema, type):
                if issubclass(schema, BaseModelV2) or issubclass(schema, BaseModelV1):
                    is_pydantic_model = True
            
            if is_pydantic_model:
                pydantic_schema = schema
            else:
                # Compile dictionary schema to dynamic Pydantic v1 model
                pydantic_schema = self._dict_to_pydantic("DynamicResponseSchema", schema)
                
            structured_llm = self.chat_model.with_structured_output(pydantic_schema)
            
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            response = await structured_llm.ainvoke(messages)
            
            # Fallback if native parsing returned None or empty dict for dict schema
            if response is None or (isinstance(schema, dict) and not response):
                return await self._generate_json_fallback(prompt, schema, system_prompt)
            
            # Format and unpack returned model/dictionary
            if isinstance(response, list) and len(response) > 0 and isinstance(response[0], dict) and "args" in response[0]:
                args = response[0]["args"]
                if isinstance(schema, list) and isinstance(args, dict) and len(args) == 1:
                    list_key = list(args.keys())[0]
                    return args[list_key]
                return args
            elif isinstance(response, BaseModel):
                res_dict = response.dict()
                if isinstance(schema, list) and len(res_dict) == 1:
                    list_key = list(res_dict.keys())[0]
                    return res_dict[list_key]
                return res_dict
            elif isinstance(response, dict):
                if isinstance(schema, list) and len(response) == 1:
                    list_key = list(response.keys())[0]
                    return response[list_key]
                return response
            
            return response
            
        except Exception as e:
            # Fallback to prompt-based extraction if API validation fails
            print(f"DEBUG: Native structured output failed (falling back to prompt-based parsing): {e}")
            return await self._generate_json_fallback(prompt, schema, system_prompt)

    def _dict_to_pydantic(self, name: str, schema: Any) -> Any:
        from pydantic import BaseModel, create_model, Field
        from typing import List, Any
        
        if isinstance(schema, list):
            if len(schema) == 1 and isinstance(schema[0], dict):
                item_model = self._dict_to_pydantic(f"{name}Item", schema[0])
                return create_model(name, items=(List[item_model], Field(default=..., description="A list of items")))
            else:
                return create_model(name, items=(List[str], Field(default=..., description="A list of items")))
                
        elif isinstance(schema, dict):
            fields = {}
            for key, val in schema.items():
                if isinstance(val, str):
                    if val == "string":
                        fields[key] = (str, ...)
                    elif val in ("boolean", "bool"):
                        fields[key] = (bool, ...)
                    elif val in ("number", "float", "int"):
                        fields[key] = (float, ...)
                    else:
                        fields[key] = (str, ...)
                elif isinstance(val, list):
                    if val and val[0] == "string":
                        fields[key] = (List[str], ...)
                    elif val and val[0] == "number":
                        fields[key] = (List[float], ...)
                    elif val and isinstance(val[0], dict):
                        sub_model = self._dict_to_pydantic(f"{name}_{key}", val[0])
                        fields[key] = (List[sub_model], ...)
                    else:
                        # Fallback to List[str] rather than List[Any] to ensure 'items' schema is populated for Gemini
                        fields[key] = (List[str], ...)
                elif isinstance(val, dict):
                    sub_model = self._dict_to_pydantic(f"{name}_{key}", val)
                    fields[key] = (sub_model, ...)
                else:
                    fields[key] = (Any, ...)
            return create_model(name, **fields)
        return create_model(name, value=(Any, ...))

    async def _generate_json_fallback(
        self,
        prompt: str,
        schema: Any,
        system_prompt: Optional[str] = None
    ) -> Any:
        # Original regex/loads fallback implementation
        json_instruction = f"""
You must respond with valid JSON only. No markdown, no explanation, just JSON.
Follow this exact schema:
{json.dumps(schema, indent=2)}
"""
        
        full_system = f"{system_prompt}\n\n{json_instruction}" if system_prompt else json_instruction
        response = await self.generate(prompt, system_prompt=full_system)
        
        # Clean response (remove markdown wrap if present)
        response = response.strip()
        import re
        if isinstance(schema, list):
            json_match = re.search(r'(\[.*\])', response, re.DOTALL)
        else:
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            
        if json_match:
            response = json_match.group(1)
        else:
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
        
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            raise LLMException(f"Failed to parse JSON response: {str(e)} | Raw response was: {response}")
    
    # Streaming using LangChain astream
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        try:
            if system_prompt:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "{input}")
                ])
            else:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("human", "{input}")
                ])
                
            chain = prompt_template | self.chat_model | StrOutputParser()
            
            async for chunk in chain.astream({"input": prompt}):
                yield chunk
                     
        except Exception as e:
            raise LLMException(f"Streaming failed: {str(e)}")
    
    # Chat with Memory (LangChain Messages history)
    def get_chat_session(self, conversation_id: str, system_prompt: Optional[str] = None) -> List[Any]:
        if conversation_id not in self._chat_sessions:
            history = []
            if system_prompt:
                history.append(SystemMessage(content=system_prompt))
            self._chat_sessions[conversation_id] = history
        return self._chat_sessions[conversation_id]
    
    async def chat(
        self,
        message: str,
        conversation_id: str,
        system_prompt: Optional[str] = None
    ) -> str:
        try:
            # Get existing history list
            history = self.get_chat_session(conversation_id, system_prompt)
            
            # Append new user message
            history.append(HumanMessage(content=message))
            
            # Invoke chat model with conversation context
            response = await self.chat_model.ainvoke(history)
            
            # Append model's response to history
            history.append(AIMessage(content=response.content))
            
            return response.content
            
        except Exception as e:
            raise LLMException(f"Chat failed: {str(e)}")
    
    def clear_chat_history(self, conversation_id: str):
        if conversation_id in self._chat_sessions:
            del self._chat_sessions[conversation_id]
    
    # Embeddings using LangChain
    async def get_embedding(self, text: str) -> List[float]:
        try:
            return await _embeddings_client.aembed_query(text)
        except Exception as e:
            raise LLMException(f"Embedding failed: {str(e)}")
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            return await _embeddings_client.aembed_documents(texts)
        except Exception as e:
            raise LLMException(f"Batch embedding failed: {str(e)}")
    
    # Function Calling (for Agents)
    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in tools
        ])
        
        full_prompt = f"""
{system_prompt or 'You are a helpful AI assistant.'}

Available tools:
{tools_desc}

If you need to use a tool, respond with:
{{
    "thought": "your reasoning",
    "action": "tool_name",
    "action_input": {{...parameters...}}
}}

If you can answer directly:
{{
    "thought": "your reasoning",
    "answer": "your response"
}}

User: {prompt}
"""
        
        response = await self.generate_json(
            prompt=full_prompt,
            schema={
                "thought": "string",
                "action": "string (optional)",
                "action_input": "object (optional)",
                "answer": "string (optional)"
            }
        )
        
        return response
    
    async def count_tokens(self, text: str) -> int:
        try:
            return self.chat_model.get_num_tokens(text)
        except Exception:
            return len(text) // 4
    
    async def is_available(self) -> bool:
        try:
            await self.generate("Say 'ok'")
            return True
        except Exception:
            return False
