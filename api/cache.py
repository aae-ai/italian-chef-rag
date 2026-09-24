from fastapi import APIRouter, HTTPException
from models.schemas import InvalidateCacheRequest
import logging
from bot import bot

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post('/cache/invalidate')
async def invalidate_cache(request: InvalidateCacheRequest):
    """Invalidate cache endpoint"""
    try:
        session_id = request.session_id
        bot.invalidate_cache(session_id)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Cache invalidate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/cache/stats')
async def cache_stats():
    """Cache statistics endpoint"""
    return bot.get_cache_stats()
