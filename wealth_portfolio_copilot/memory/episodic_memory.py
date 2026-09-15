"""Episodic Memory - Short-term conversation context management."""

from typing import List, Dict, Any
from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None


class EpisodicMemory:
    """
    Maintains short-term conversation context.
    Uses a sliding window to keep only recent turns.
    """
    
    def __init__(self, max_turns: int = 10):
        """
        Initialize episodic memory.
        
        Args:
            max_turns: Maximum number of conversation turns to remember
        """
        self.max_turns = max_turns
        self.conversation_history = deque(maxlen=max_turns * 2)  # 2 messages per turn
        self.session_id = None
        self.started_at = datetime.now()
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (e.g., entities detected, intent)
        """
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.conversation_history.append(message)
    
    def get_context(self, num_turns: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve conversation context for the LLM.
        
        Args:
            num_turns: Number of recent turns to retrieve (default: all)
            
        Returns:
            List of message dictionaries in OpenAI format
        """
        messages = []
        limit = len(self.conversation_history)
        if num_turns:
            limit = min(limit, num_turns * 2)
        
        for msg in list(self.conversation_history)[-limit:]:
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            })
        
        return messages
    
    def get_context_summary(self) -> str:
        """
        Generate a summary of the current conversation context.
        
        Returns:
            String summarizing the conversation topics
        """
        if not self.conversation_history:
            return "No conversation history."
        
        topics = []
        for msg in self.conversation_history:
            if msg.role == 'user':
                # Extract key topics (simplified - would use NLP in production)
                topics.append(msg.content[:50])
        
        return f"Conversation topics: {', '.join(topics[-3:])}"
    
    def clear(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()
        self.started_at = datetime.now()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_messages": len(self.conversation_history),
            "session_duration": str(datetime.now() - self.started_at),
            "max_capacity": self.max_turns
        }
