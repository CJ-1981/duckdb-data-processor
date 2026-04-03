"""
FastAPI Application Main module

Creates the main FastAPI application instance with middleware stack,
 routers, and lifecycle events, and OpenAPI documentation.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config.loader import Config
from src.api.dependencies import get_processor, get_config
from src.api.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    ErrorHandlerMiddleware
)
from src.api.routes.system import router as health_router
from src.api.routes.users import router as users_router
from src.api.routes.data import router as data_router
from src.api.routes.workflows import router as workflows_router
from src.api.routes.jobs import router as jobs_router


# Configure logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting DuckDB Data Processor API...")

    # Initialize processor singleton
    processor_gen = get_processor()
    processor = next(processor_gen)
    app.state.processor = processor
    logger.info("Processor initialized")

    yield

    # Shutdown
    logger.info("Shutting down DuckDB Data Processor API...")

    # Close processor if exists
    processor = app.state.processor
    if processor:
        processor.close()

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application instance"""
    app = FastAPI(
        title="DuckDB Data Processor API",
        version="1.0.0",
        description="Full-stack data analysis platform powered by DuckDB",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Load configuration
    config = get_config()

    # Configure CORS middleware
    # @MX:NOTE: CORS must to be configured from config
    # Default CORS settings - will be overridden by config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Default: allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware stack
    # Note: Order matters - outer to inner
    # 1. CORS (first) - already added above
    # 2. Request ID
    app.add_middleware(RequestIDMiddleware)
    # 3. Logging
    app.add_middleware(LoggingMiddleware)
    # 4. Error Handler
    app.add_middleware(ErrorHandlerMiddleware)
    # 5. Authentication (will be added in later task)

    # Register routers
    # Note: Additional routers will be added in later tasks (auth, jobs, etc.)
    app.include_router(health_router)    # System configuration endpoints
    app.include_router(users_router)     # User management endpoints
    app.include_router(data_router)      # Data processing endpoints
    app.include_router(workflows_router) # Workflow management endpoints
    app.include_router(jobs_router)      # Job execution endpoints

    # Root endpoints
    @app.get("/")
    async def root():
        """Root endpoint returning API information"""
        return {
            "message": "DuckDB Data Processor API",
            "version": "1.0.0",
            "documentation": "/docs"
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}

    return app


# Create the global app instance
# @MX:ANCHOR: Global FastAPI app instance for test imports and module access
# @MX:REASON: Tests expect direct `app` export, not factory function
app = create_app()
