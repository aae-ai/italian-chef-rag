from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
import logging
from bot import bot

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get('/metrics', response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    return bot.metrics()

@router.get('/stats')
async def stats():
    """System statistics endpoint"""
    return bot.get_stats()
