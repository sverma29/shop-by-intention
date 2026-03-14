"""
Pydantic models for API requests.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class ShopRequest(BaseModel):
    """Request model for shopping queries."""
    query: str = Field(..., description="User's natural language shopping query")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")


class BenchmarkRequest(BaseModel):
    """Request model for benchmark tests."""
    queries: Optional[List[str]] = Field(None, description="Optional list of queries to test")