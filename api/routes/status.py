"""
Status and monitoring API endpoints for version 1.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from api.models.response import StatusResponse, EventResponse
from api.services.shop_service import shop_service

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_system_status():
    """
    Get the current status of the SHOP-BY-INTENTION system.
    
    Returns:
        System status and component health information
    """
    try:
        result = shop_service.get_system_status()
        
        return StatusResponse(
            status=result["status"],
            timestamp=result["timestamp"],
            uptime=result["uptime"],
            version=result["version"],
            components=result["components"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting system status: {str(e)}"
        )


@router.get("/events", response_model=EventResponse)
async def get_event_logs(event_type: Optional[str] = None):
    """
    Get event logs and statistics from the system.
    
    Args:
        event_type: Optional event type to filter by
        
    Returns:
        Event logs and system statistics
    """
    try:
        result = shop_service.get_event_logs(event_type)
        
        return EventResponse(
            events=result["events"],
            statistics=result["statistics"],
            total_events=result["total_events"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting event logs: {str(e)}"
        )