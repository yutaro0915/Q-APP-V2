"""API routers package.

This package contains all FastAPI routers for the Kyudai Campus SNS API.
Each router module handles a specific domain of the API.

Router Registration:
    Routers should be imported in main.py and registered with the app instance
    using app.include_router() with appropriate prefixes.

Example:
    from app.routers import health, threads, comments
    
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(threads.router, prefix="/api/v1")
    app.include_router(comments.router, prefix="/api/v1")
"""

from . import health, threads

__all__ = [
    "health",
    "threads",
]