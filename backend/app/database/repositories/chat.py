"""
========================================
Chat Repository
========================================
Database operations for chat history
"""

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import json

from app.database.models import Conversation, Message, MessageRole
from app.database.connection import AsyncSessionLocal


class ChatRepository:
    """Repository for managing chat data"""
    
    async def create_conversation(self, title: str = "New Conversation") -> str:
        """Create a new conversation"""
        import uuid
        
        conversation_id = str(uuid.uuid4())
        
        async with AsyncSessionLocal() as session:
            conversation = Conversation(
                id=conversation_id,
                title=title
            )
            session.add(conversation)
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
    ) -> Message:
        """Add a message to a conversation"""
        async with AsyncSessionLocal() as session:
            # Verify conversation exists
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                # Create if doesn't exist (auto-create)
                conversation = Conversation(id=conversation_id, title=content[:50])
                session.add(conversation)
            
            # Create message
            message = Message(
                conversation_id=conversation_id,
                role=MessageRole(role),
                content=content,
                sources_json=json.dumps(sources) if sources else None,
                confidence=confidence,
                agent_steps_json=json.dumps(agent_steps) if agent_steps else None
            )
            
            session.add(message)
            await session.commit()
            await session.refresh(message)
            
            return message
    
    async def get_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history formatted for LLM"""
        async with AsyncSessionLocal() as session:
            stmt = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).limit(limit)
            
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            return [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                }
                for msg in messages
            ]
    
    async def get_full_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get full history with metadata for frontend"""
        async with AsyncSessionLocal() as session:
            stmt = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc())
            
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            history = []
            for msg in messages:
                item = {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                }
                
                if msg.sources_json:
                    item["sources"] = json.loads(msg.sources_json)
                
                if msg.agent_steps_json:
                    item["agent_steps"] = json.loads(msg.agent_steps_json)
                
                history.append(item)
            
            return history


# Global instance
chat_repo = ChatRepository()
