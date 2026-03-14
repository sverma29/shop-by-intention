"""
FastAPI application for SHOP-BY-INTENTION system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from api.api.v1 import shop, status, health

# Create FastAPI app
app = FastAPI(
    title="SHOP-BY-INTENTION API",
    description="Agentic shopping system API for natural language queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(shop.router, prefix="/api/v1")
app.include_router(status.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")

# Serve static files (frontend)
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page."""
    try:
        with open(os.path.join(frontend_dir, "index.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>SHOP-BY-INTENTION API</h1><p>Frontend not found. Use the API endpoints directly.</p>",
            status_code=200
        )


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with enhanced styling."""
    return app.openapi()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )