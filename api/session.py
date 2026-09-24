from fastapi import APIRouter
import logging
from bot import bot

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get('/session/{session_id}/history')
async def session_history(session_id: str):
    """Get session history endpoint"""
    # Note: Accessing session_manager directly from bot to avoid complex refactor for now
    # but eventually this can be a direct dependency.
    history = bot.session_manager.get_messages(session_id)
    return history

@router.post('/session/{session_id}/clear')
async def clear_session(session_id: str):
    """Clear session endpoint"""
    success = bot.session_manager.clear(session_id)
    return {"status": "success" if success else "failed"}
