from fastapi import APIRouter
import logging
from bot import bot

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get('/health')
async def health():
    """Health check endpoint"""
    health_status = bot.health_check()
    return health_status
