from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, SourceModel
import asyncio
import logging
from bot import bot

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post('/chat', response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with ChefBot - properly async"""
    try:
        user_input = request.message
        session_id = request.session_id

        logger.info(f"Received chat request: {user_input[:80]}...")

        # Run bot.ask in a thread as it's not natively async yet
        response = await asyncio.to_thread(bot.ask, user_input, session_id)

        return ChatResponse(
            response=response.answer,
            session_id=response.session_id,
            sources=[
                SourceModel(content=s.content, source=s.source, score=s.score)
                for s in response.sources
            ],
            cached=response.cached,
            latency_ms=round(response.latency_ms, 2)
        )
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
