import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.cache import router as cache_router

# Import Routers
from api.chat import router as chat_router
from api.health import router as health_router
from api.metrics import router as metrics_router
from api.session import router as session_router

# Import Core
from middleware.security import setup_security

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI"""
    logger.info("Starting ChefBot application...")
    # Initialize the bot eagerly so first request is fast
    from bot import bot

    logger.info(
        f"ChefBot engine ready. Uptime: {round(time.time() - bot.start_time, 2)}s"
    )
    yield
    logger.info("Shutting down ChefBot application...")


def create_app():
    """Application factory"""
    app = FastAPI(
        title="ChefBot API",
        description="Italian Chef Bot - RAG-powered recipe assistant",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Setup security middleware
    setup_security(app)

    # Static files and Templates
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")

    # Register Routers
    app.include_router(chat_router, tags=["Chat"])
    app.include_router(health_router, tags=["Health"])
    app.include_router(metrics_router, tags=["Metrics"])
    app.include_router(cache_router, tags=["Cache"])
    app.include_router(session_router, tags=["Session"])

    # Web Interface
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """Serve the main web interface"""
        import uuid
        return templates.TemplateResponse(
            request=request, 
            name="index.html", 
            context={
                "request": request,
                "initial_session_id": str(uuid.uuid4())
            }
        )

    @app.get("/api-spec")
    async def api_spec():
        """Serve OpenAPI specification as JSON"""
        return app.openapi()

    return app
