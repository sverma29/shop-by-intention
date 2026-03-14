"""
Pydantic models for API responses.
"""

from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime


class ShopResponse(BaseModel):
    """Response model for shopping results."""
    user_query: str
    final_intent: Dict[str, Any]
    final_cart: Dict[str, Any]
    loop_count: int
    processing_time: float
    timestamp: str


class StatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    timestamp: str
    uptime: str
    version: str
    components: Dict[str, str]


class EventResponse(BaseModel):
    """Response model for event logs."""
    events: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    total_events: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str


class BenchmarkResponse(BaseModel):
    """Response model for benchmark results."""
    benchmark_result: Dict[str, Any]
    processing_time: float
    timestamp: str