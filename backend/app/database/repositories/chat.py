# Chat Repository
# Database operations for chat history

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from app.database.connection import AsyncSessionLocal


class ChatRepository:
    """Repository for managing chat data"""
    
    async def create_conversation(self, title: str = "New Conversation") -> str:
        # Create a new conversation
        import uuid
        
        conversation_id = str(uuid.uuid4())
        
        async with AsyncSessionLocal() as session:
            stmt = text("""
                INSERT INTO conversations (id, title, created_at, updated_at) 
                VALUES (:id, :title, :created_at, :updated_at)
            """)
            now = datetime.utcnow()
            await session.execute(stmt, {
                "id": conversation_id,
                "title": title,
                "created_at": now,
                "updated_at": now
            })
            await session.commit()
            
            return conversation_id
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: List[Dict] = None,
        confidence: float = None,
        agent_steps: List[Dict] = None
    ) -> None:
        # Add a message to a conversation
        async with AsyncSessionLocal() as session:
            # Verify conversation exists
            stmt = text("SELECT id FROM conversations WHERE id = :id")
            result = await session.execute(stmt, {"id": conversation_id})
            conversation_exists = result.scalar() is not None
            
            now = datetime.utcnow()
            if not conversation_exists:
                # Create if doesn't exist (auto-create)
                insert_conv_stmt = text("""
                    INSERT INTO conversations (id, title, created_at, updated_at)
                    VALUES (:id, :title, :created_at, :updated_at)
                """)
                await session.execute(insert_conv_stmt, {
                    "id": conversation_id,
                    "title": content[:50],
                    "created_at": now,
                    "updated_at": now
                })
            
            # Create message
            insert_msg_stmt = text("""
                INSERT INTO messages (conversation_id, role, content, sources_json, confidence, agent_steps_json, created_at)
                VALUES (:conversation_id, :role, :content, :sources_json, :confidence, :agent_steps_json, :created_at)
            """)
            await session.execute(insert_msg_stmt, {
                "conversation_id": conversation_id,
                "role": role.upper(),
                "content": content,
                "sources_json": json.dumps(sources) if sources else None,
                "confidence": confidence,
                "agent_steps_json": json.dumps(agent_steps) if agent_steps else None,
                "created_at": now
            })
            await session.commit()
            
            return None
    
    async def get_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        # Get conversation history formatted for LLM
        async with AsyncSessionLocal() as session:
            stmt = text("""
                SELECT role, content, created_at 
                FROM messages 
                WHERE conversation_id = :conversation_id 
                ORDER BY created_at ASC 
                LIMIT :limit
            """)
            result = await session.execute(stmt, {"conversation_id": conversation_id, "limit": limit})
            messages = result.all()
            
            return [
                {
                    "role": msg.role.lower() if msg.role else msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if hasattr(msg.created_at, "isoformat") else str(msg.created_at)
                }
                for msg in messages
            ]
    
    async def get_full_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        # Get full history with metadata for frontend
        async with AsyncSessionLocal() as session:
            stmt = text("""
                SELECT id, role, content, sources_json, agent_steps_json, created_at 
                FROM messages 
                WHERE conversation_id = :conversation_id 
                ORDER BY created_at ASC
            """)
            result = await session.execute(stmt, {"conversation_id": conversation_id})
            messages = result.all()
            
            history = []
            for msg in messages:
                item = {
                    "id": msg.id,
                    "role": msg.role.lower() if msg.role else msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if hasattr(msg.created_at, "isoformat") else str(msg.created_at)
                }
                
                if msg.sources_json:
                    item["sources"] = json.loads(msg.sources_json)
                
                if msg.agent_steps_json:
                    item["agent_steps"] = json.loads(msg.agent_steps_json)
                
                history.append(item)
            
            return history


# Global instance
chat_repo = ChatRepository()
