from pydantic import BaseModel
from typing import List, Optional
from dataclasses import dataclass

# =============================================================================
# DATA CLASSES (for internal logic)
# =============================================================================

@dataclass
class SourceDocument:
    """Represents a retrieved source document"""
    content: str
    source: str
    score: float = 0.0

@dataclass
class ChefBotResponse:
    """Structured response with metadata"""
    answer: str
    sources: List[SourceDocument]
    session_id: str
    cached: bool = False
    latency_ms: float = 0.0

# =============================================================================
# PYDANTIC MODELS (for API validation)
# =============================================================================

class SourceModel(BaseModel):
    content: str
    source: str
    score: float

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[SourceModel]
    cached: bool
    latency_ms: float

class InvalidateCacheRequest(BaseModel):
    session_id: Optional[str] = None
