"""
Shop service for handling shopping queries through the agentic system.
"""

import time
import sys
import os
import json
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
from core.events.event_logger import get_event_statistics
from core.events.event_context import set_session_id


class ShopService:
    """Service for processing shopping queries through the agentic system."""
    
    def __init__(self):
        self.max_loops = 5
        self.test_cases = self._load_test_cases()
    
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
        
        # Initialize context trace session
        trace_id = set_session_id(session_id)
        
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
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load standardized test cases for evaluation."""
        try:
            import json
            
            # Path to benchmark queries file
            test_cases_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "data", "benchmark_queries.json"
            )
            
            with open(test_cases_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Test cases file not found at {test_cases_file}")
            return []
        except Exception as e:
            print(f"Error loading test cases: {e}")
            return []
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query string for better matching."""
        import re
        
        # Basic normalization for exact matching
        normalized = query.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        
        return normalized

    def _find_test_case(self, query: str) -> Optional[Dict[str, Any]]:
        """Find matching test case for a query with strict predefined matching."""
        if not self.test_cases:
            return None
        
        # Normalize query for matching
        query_normalized = self._normalize_query(query)
        
        # Try exact match first (strict predefined matching)
        for test_case in self.test_cases:
            test_query = test_case.get("query", "")
            test_normalized = self._normalize_query(test_query)
            
            if query_normalized == test_normalized:
                return test_case
        
        # If no exact match, return None (don't try partial matching)
        return None
    
    def _check_budget_compliance(self, actual_result: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """Check if actual result complies with expected budget."""
        expected_budget = expected.get("budget")
        if not expected_budget:
            return True  # No budget constraint to check
        
        actual_total = actual_result["final_cart"].get("total_cost", 0)
        return actual_total <= expected_budget
    
    def _check_product_match(self, actual_result: Dict[str, Any], expected_products: List[str]) -> bool:
        """Check if actual products match expected products."""
        if not expected_products:
            return True  # No specific products expected
        
        actual_products = [item.get("id") for item in actual_result["final_cart"].get("items", [])]
        
        # Check if at least one actual product is in the expected products list
        return any(product in expected_products for product in actual_products) and len(actual_products) > 0
    
    def _calculate_query_score(self, category_match: bool, budget_compliant: bool, products_match: bool) -> float:
        """Calculate overall score for a query evaluation."""
        # Weighted scoring
        category_weight = 0.4
        budget_weight = 0.3
        products_weight = 0.3
        
        score = (
            (1.0 if category_match else 0.0) * category_weight +
            (1.0 if budget_compliant else 0.0) * budget_weight +
            (1.0 if products_match else 0.0) * products_weight
        )
        
        return round(score, 2)
    
    def _identify_issues(self, category_match: bool, budget_compliant: bool, products_match: bool) -> List[str]:
        """Identify specific issues in query evaluation."""
        issues = []
        
        if not category_match:
            issues.append("Category mismatch - system identified wrong product category")
        
        if not budget_compliant:
            issues.append("Budget exceeded - cart total exceeds specified budget")
        
        if not products_match:
            issues.append("Product mismatch - expected products not included in cart")
        
        return issues
    
    def _evaluate_query_result(self, query: str, actual_result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single query result against expected outcomes."""
        
        # Find matching test case
        test_case = self._find_test_case(query)
        
        if not test_case:
            return {
                "query": query,
                "expected": None,
                "actual": actual_result,
                "evaluation": {
                    "category_match": False,
                    "budget_compliant": False,
                    "products_match": False,
                    "score": 0.0,
                    "issues": [f"Query not predefined: '{query}'. Please use predefined benchmark queries."]
                }
            }
        
        expected = test_case["expected_intent"]
        expected_products = test_case.get("expected_products", [])
        
        # Calculate evaluation metrics
        category_match = expected["category"] == actual_result["final_intent"].get("category")
        budget_compliant = self._check_budget_compliance(actual_result, expected)
        products_match = self._check_product_match(actual_result, expected_products)
        
        # Calculate overall score
        score = self._calculate_query_score(category_match, budget_compliant, products_match)
        
        return {
            "query": query,
            "expected": expected,
            "actual": actual_result,
            "evaluation": {
                "category_match": category_match,
                "budget_compliant": budget_compliant,
                "products_match": products_match,
                "score": score,
                "issues": self._identify_issues(category_match, budget_compliant, products_match)
            }
        }
    
    def _calculate_evaluation_metrics(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall evaluation metrics."""
        
        if not evaluations:
            return {
                "overall_accuracy": 0.0,
                "category_accuracy": 0.0,
                "budget_compliance": 0.0,
                "product_relevance": 0.0,
                "completeness_score": 0.0
            }
        
        # Calculate individual metric accuracies
        total_evaluations = len(evaluations)
        
        category_accuracy = sum(1 for e in evaluations if e["evaluation"]["category_match"]) / total_evaluations
        budget_compliance = sum(1 for e in evaluations if e["evaluation"]["budget_compliant"]) / total_evaluations
        product_relevance = sum(1 for e in evaluations if e["evaluation"]["products_match"]) / total_evaluations
        
        # Calculate overall accuracy (weighted average)
        overall_accuracy = (category_accuracy * 0.4 + budget_compliance * 0.3 + product_relevance * 0.3)
        
        return {
            "overall_accuracy": round(overall_accuracy, 2),
            "category_accuracy": round(category_accuracy, 2),
            "budget_compliance": round(budget_compliance, 2),
            "product_relevance": round(product_relevance, 2),
            "completeness_score": round(overall_accuracy, 2)
        }
    
    def run_benchmark(self, queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run benchmark tests on the system with comprehensive evaluation."""
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
        
        # Calculate basic metrics
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
        
        # Enhanced evaluation
        evaluations = []
        for i, result in enumerate(results):
            query = queries[i]
            evaluation = self._evaluate_query_result(query, result)
            evaluations.append(evaluation)
        
        # Calculate evaluation metrics
        evaluation_metrics = self._calculate_evaluation_metrics(evaluations)
        
        result_data = {
            "metrics": metrics,
            "evaluation": evaluation_metrics,
            "individual_results": evaluations,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Append results to evaluation JSON
        try:
            eval_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "evaluation"
            )
            os.makedirs(eval_dir, exist_ok=True)
            eval_file = os.path.join(eval_dir, "benchmark_results.json")
            
            all_results = []
            if os.path.exists(eval_file):
                try:
                    with open(eval_file, "r") as f:
                        all_results = json.load(f)
                        if not isinstance(all_results, list):
                            all_results = [all_results]
                except json.JSONDecodeError:
                    pass
                    
            all_results.append(result_data)
            
            with open(eval_file, "w") as f:
                json.dump(all_results, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save benchmark results to JSON: {e}")
        
        return result_data

# Global shop service instance
shop_service = ShopService()