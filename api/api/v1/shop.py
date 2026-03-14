"""
Shop API endpoints for version 1.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List

from api.models.request import ShopRequest, BenchmarkRequest
from api.models.response import ShopResponse, BenchmarkResponse
from api.services.shop_service import shop_service

router = APIRouter(tags=["shop"])


@router.post("/shop", response_model=ShopResponse)
async def process_shopping_query(request: ShopRequest):
    """
    Process a user's shopping query through the agentic system.
    
    Args:
        request: User query and optional session ID
        
    Returns:
        Shopping results with intent, cart, and processing information
    """
    try:
        result = shop_service.process_query(request.query, request.session_id)
        
        return ShopResponse(
            user_query=result["user_query"],
            final_intent=result["final_intent"],
            final_cart=result["final_cart"],
            loop_count=result["loop_count"],
            processing_time=result["processing_time"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing shopping query: {str(e)}"
        )


@router.post("/benchmark", response_model=BenchmarkResponse)
async def run_benchmark(request: BenchmarkRequest):
    """
    Run benchmark tests on the system.
    
    Args:
        request: Optional list of queries to test
        
    Returns:
        Benchmark results and metrics
    """
    try:
        result = shop_service.run_benchmark(request.queries)
        
        return BenchmarkResponse(
            benchmark_result=result["metrics"],
            processing_time=result["processing_time"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running benchmark: {str(e)}"
        )