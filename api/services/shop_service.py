"""
Shop service for handling shopping queries through the agentic system.
"""

import time
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add the parent directory to Python path to find core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the current directory to Python path to find api modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the grandparent directory to Python path for uvicorn running from api/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.agents.intent_agent import parse_intent
from core.agents.retrieval_agent import retrieve_products
from core.agents.reasoning_agent import reason_products
from core.agents.cart_agent import build_cart
from core.agents.evaluation_agent import evaluate_cart
from core.loops.loop_controller import control_loop, reset_loop
from core.events.event_logger import get_event_statistics, clear_logs


class ShopService:
    """Service for processing shopping queries through the agentic system."""
    
    def __init__(self):
        self.max_loops = 5
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user query through the complete agentic workflow.
        
        Args:
            query: User's natural language query
            session_id: Optional session ID for tracking
            
        Returns:
            Complete system result with final cart and reasoning
        """
        # Reset for new query
        reset_loop()
        clear_logs()
        
        # Initialize state
        intent_state: Optional[Dict[str, Any]] = None
        cart_state: Dict[str, Any] = {"items": [], "total_cost": 0, "is_stable": False}
        loop_count = 0
        
        start_time = time.time()
        
        # Main agentic loop
        while loop_count < self.max_loops:
            loop_count += 1
            
            # Step 1: Intent Parsing
            if not intent_state:
                intent_state = parse_intent(query)
            
            # Step 2: Product Retrieval
            candidates = retrieve_products(intent_state)
            
            # Step 3: Reasoning
            reasoning_result = reason_products(intent_state, candidates)
            
            # Step 4: Cart Building
            cart_state = build_cart(reasoning_result, intent_state)
            
            # Step 5: Evaluation
            evaluation_result = evaluate_cart(cart_state, intent_state)
            
            # Step 6: Loop Control
            should_continue, next_action, loop_info = control_loop(
                intent_state, evaluation_result, cart_state
            )
            
            # Check termination conditions
            if not should_continue or not evaluation_result['should_continue']:
                break
            
            # If we need to adjust intent, clear current intent to trigger refinement
            if next_action == "refine_intent":
                intent_state = None
        
        processing_time = time.time() - start_time
        
        # Prepare final result
        final_result = {
            "user_query": query,
            "final_intent": intent_state,
            "final_cart": cart_state,
            "loop_count": loop_count,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return final_result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the current status of the SHOP-BY-INTENTION system."""
        try:
            # Get event statistics
            stats = get_event_statistics()
            
            # Calculate uptime (approximate)
            uptime_seconds = time.time()
            
            return {
                "status": "operational",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": f"{uptime_seconds:.0f} seconds",
                "version": "1.0.0",
                "components": {
                    "intent_agent": "operational",
                    "retrieval_agent": "operational", 
                    "reasoning_agent": "operational",
                    "cart_agent": "operational",
                    "evaluation_agent": "operational",
                    "loop_controller": "operational",
                    "event_logger": "operational"
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_event_logs(self, event_type: Optional[str] = None) -> Dict[str, Any]:
        """Get event logs and statistics from the system."""
        try:
            from core.events.event_model import EventType
            
            # Convert string event type to enum if provided
            event_type_enum = None
            if event_type:
                try:
                    event_type_enum = EventType(event_type)
                except ValueError:
                    raise ValueError(f"Invalid event type: {event_type}")
            
            # Get events
            from core.events.event_logger import get_events
            events = get_events(event_type=event_type_enum)
            
            # Get statistics
            statistics = get_event_statistics()
            
            return {
                "events": events,
                "statistics": statistics,
                "total_events": len(events)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "events": [],
                "statistics": {},
                "total_events": 0
            }
    
    def run_benchmark(self, queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run benchmark tests on the system."""
        if queries is None:
            queries = [
                "I want a gaming laptop under $1500",
                "I need a cheap camera for photography",
                "I want a portable coding laptop",
                "Build a home office setup under $1000"
            ]
        
        results = []
        start_time = time.time()
        
        for query in queries:
            result = self.process_query(query)
            results.append(result)
        
        processing_time = time.time() - start_time
        
        # Calculate metrics
        metrics = {
            "total_queries": len(queries),
            "successful_completions": len([r for r in results if r["final_cart"].get("items")]),
            "average_loops": sum(r["loop_count"] for r in results) / len(results),
            "average_processing_time": sum(r["processing_time"] for r in results) / len(results)
        }
        
        if metrics["successful_completions"] > 0:
            metrics["average_cart_value"] = sum(
                r["final_cart"]["total_cost"] for r in results 
                if r["final_cart"].get("items")
            ) / metrics["successful_completions"]
        else:
            metrics["average_cart_value"] = 0
        
        return {
            "metrics": metrics,
            "individual_results": results,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global shop service instance
shop_service = ShopService()