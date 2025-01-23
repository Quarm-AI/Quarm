from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from collections import deque

class ConversationMemory:
    def __init__(self, max_history: int = 10, max_age_hours: int = 24):
        # Store conversations per user
        self._conversations: Dict[str, deque] = {}
        self.max_history = max_history
        self.max_age = timedelta(hours=max_age_hours)
        self._cleanup_task = None
    
    def start_cleanup(self):
        """Start the cleanup task if it's not already running"""
        if self._cleanup_task is None:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(self._periodic_cleanup())
    
    def add_exchange(self, user_id: str, query: str, response: str):
        """Add a query-response pair to the user's conversation history"""
        if user_id not in self._conversations:
            self._conversations[user_id] = deque(maxlen=self.max_history)
            
        self._conversations[user_id].append({
            'timestamp': datetime.now(),
            'query': query,
            'response': response
        })
    
    def get_context(self, user_id: str, max_items: int = 3) -> str:
        """Get recent conversation context for a user"""
        if user_id not in self._conversations:
            return ""
            
        recent = list(self._conversations[user_id])[-max_items:]
        
        context_parts = []
        for exchange in recent:
            context_parts.append(f"User: {exchange['query']}")
            context_parts.append(f"Assistant: {exchange['response']}\n")
            
        return "\n".join(context_parts)
    
    async def _periodic_cleanup(self):
        """Periodically remove old conversations"""
        while True:
            now = datetime.now()
            for user_id in list(self._conversations.keys()):
                while self._conversations[user_id]:
                    oldest = self._conversations[user_id][0]
                    if now - oldest['timestamp'] > self.max_age:
                        self._conversations[user_id].popleft()
                    else:
                        break
                        
                if not self._conversations[user_id]:
                    del self._conversations[user_id]
                    
            await asyncio.sleep(3600)  # Cleanup every hour 