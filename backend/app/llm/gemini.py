# Gemini LLM Client
# Integration with Google's Gemini API

import google.generativeai as genai
from typing import Optional, List, Dict, Any, AsyncGenerator
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.exceptions import LLMException


class GeminiClient:
    # Client for Google Gemini API
    # Features: Text generation, Structured output, Streaming, Function calling, Retry logic
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        
        if not self.api_key:
            raise LLMException("GEMINI_API_KEY is required")
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        self.model = genai.GenerativeModel(
            model_name=settings.LLM_MODEL,
            generation_config={
                "temperature": settings.LLM_TEMPERATURE,
                "max_output_tokens": settings.LLM_MAX_TOKENS,
                "top_p": 0.95,
                "top_k": 40
            }
        )
        
        # Chat session storage
        self._chat_sessions: Dict[str, Any] = {}
    
    # Basic Generation
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        # Generate text response from prompt
        print(f"--- Gemini Generating with model: {settings.LLM_MODEL} ---")
        try:
            # Build full prompt
            full_prompt = ""
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n"
            full_prompt += prompt
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt
            )
            
            return response.text
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            with open("last_gemini_error.txt", "w", encoding="utf-8") as f:
                f.write(error_msg)
            
            print(f"\n\n🚨 ============= GEMINI ERROR START ============= 🚨")
            print(f"Model used: {settings.LLM_MODEL}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            if hasattr(e, "status_code"):
                print(f"Status Code: {e.status_code}")
            
            # Print full traceback to console
            print(error_msg)
            print(f"🚨 ================= GEMINI ERROR END ================= 🚨\n\n")
            
            raise LLMException(f"Generation failed: {str(e)}")
    
    # Structured Output
    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        # Generate structured JSON output
        json_instruction = f"""
You must respond with valid JSON only. No markdown, no explanation, just JSON.
Follow this exact schema:
{json.dumps(schema, indent=2)}
"""
        
        full_system = f"{system_prompt}\n\n{json_instruction}" if system_prompt else json_instruction
        
        response = await self.generate(prompt, system_prompt=full_system)
        
        # Clean response (remove markdown if present)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            raise LLMException(f"Failed to parse JSON response: {str(e)}")
    
    # Streaming
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        # Stream text response token by token
        try:
            full_prompt = ""
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n"
            full_prompt += prompt
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            raise LLMException(f"Streaming failed: {str(e)}")
    
    # Chat with Memory
    def get_chat_session(self, conversation_id: str):
        # Get or create a chat session
        if conversation_id not in self._chat_sessions:
            self._chat_sessions[conversation_id] = self.model.start_chat(history=[])
        return self._chat_sessions[conversation_id]
    
    async def chat(
        self,
        message: str,
        conversation_id: str,
        system_prompt: Optional[str] = None
    ) -> str:
        # Chat with conversation memory
        try:
            chat = self.get_chat_session(conversation_id)
            
            # Add system prompt if first message
            if system_prompt and len(chat.history) == 0:
                await asyncio.to_thread(
                    chat.send_message,
                    f"System: {system_prompt}"
                )
            
            response = await asyncio.to_thread(
                chat.send_message,
                message
            )
            
            return response.text
            
        except Exception as e:
            raise LLMException(f"Chat failed: {str(e)}")
    
    def clear_chat_history(self, conversation_id: str):
        # Clear chat history for a conversation
        if conversation_id in self._chat_sessions:
            del self._chat_sessions[conversation_id]
    
    # Embeddings
    async def get_embedding(self, text: str) -> List[float]:
        # Get embedding vector for text
        try:
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
            
        except Exception as e:
            raise LLMException(f"Embedding failed: {str(e)}")
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        # Get embeddings for multiple texts
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    # Function Calling (for Agents)
    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        # Generate response with function/tool calling capability
        # Format tools description
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
    
    # Utilities
    async def count_tokens(self, text: str) -> int:
        # Count tokens in text
        try:
            result = await asyncio.to_thread(
                self.model.count_tokens,
                text
            )
            return result.total_tokens
        except Exception:
            # Rough estimate if counting fails
            return len(text) // 4
    
    async def is_available(self) -> bool:
        # Check if the API is available
        try:
            await self.generate("Say 'ok'")
            return True
        except Exception:
            return False
