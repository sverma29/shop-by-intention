"""
Health check API endpoints for version 1.
"""

from fastapi import APIRouter
from datetime import datetime

from api.models.response import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify the system is operational.
    
    Returns:
        System health status and timestamp
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )