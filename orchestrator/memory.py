"""
Conversation memory for multi-turn interactions
"""

from typing import List, Dict
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class ItineraryMemory:
    """
    Manages conversation history for the itinerary planning system
    """
    
    def __init__(self):
        self.history = ChatMessageHistory()
        self.memory = ConversationBufferMemory(
            chat_memory=self.history,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Store structured context from previous interactions
        self.user_context_history: List[Dict] = []
        self.itinerary_versions: List[Dict] = []
    
    def add_user_message(self, message: str):
        """Add user message to history"""
        self.history.add_user_message(message)
    
    def add_ai_message(self, message: str):
        """Add AI response to history"""
        self.history.add_ai_message(message)
    
    def add_system_message(self, message: str):
        """Add system message to history"""
        self.history.add_message(SystemMessage(content=message))
    
    def store_user_context(self, context: Dict):
        """Store extracted user context"""
        self.user_context_history.append({
            "timestamp": context.get("timestamp"),
            "context": context
        })
    
    def store_itinerary(self, itinerary: Dict, version: str = "draft"):
        """Store generated itinerary"""
        self.itinerary_versions.append({
            "version": version,
            "itinerary": itinerary,
            "timestamp": itinerary.get("created_at")
        })
    
    def get_latest_context(self) -> Dict:
        """Get most recent user context"""
        if self.user_context_history:
            return self.user_context_history[-1]["context"]
        return {}
    
    def get_latest_itinerary(self) -> Dict:
        """Get most recent itinerary"""
        if self.itinerary_versions:
            return self.itinerary_versions[-1]["itinerary"]
        return {}
    
    def get_chat_history(self) -> List:
        """Get chat message history"""
        return self.history.messages
    
    def clear(self):
        """Clear all memory"""
        self.history.clear()
        self.user_context_history.clear()
        self.itinerary_versions.clear()
    
    def summary(self) -> Dict:
        """Get memory summary"""
        return {
            "total_messages": len(self.history.messages),
            "context_versions": len(self.user_context_history),
            "itinerary_versions": len(self.itinerary_versions),
            "latest_context": self.get_latest_context(),
            "has_itinerary": len(self.itinerary_versions) > 0
        }
