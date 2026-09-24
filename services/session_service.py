import logging
from typing import List, Dict
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from core.config import Config

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages chat sessions with MongoDB"""

    def __init__(self):
        self.connection_string = Config.MONGO_URI
        self.database_name = Config.MONGO_DB_NAME
        self.collection_name = Config.MONGO_COLLECTION_NAME

    def get_history(self, session_id: str):
        """Get MongoDB chat history for a session"""
        return MongoDBChatMessageHistory(
            session_id=session_id,
            connection_string=self.connection_string,
            database_name=self.database_name,
            collection_name=self.collection_name,
            create_index=True,
        )

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        """Get chat history as list of messages"""
        try:
            history = self.get_history(session_id)
            return [
                {"type": msg.type, "content": msg.content}
                for msg in history.messages
            ]
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []

    def clear(self, session_id: str) -> bool:
        """Delete all messages for a session"""
        try:
            history = self.get_history(session_id)
            history.clear()
            logger.info(f"Cleared session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False

    def health_check(self) -> bool:
        """Check if MongoDB connection is healthy"""
        try:
            test_history = self.get_history("health-check-test")
            _ = test_history.messages  # Force connection
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
