"""
Main orchestrator for SHOP-BY-INTENTION System

Coordinates all agents and manages the complete agentic workflow.
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from agents.intent_agent import parse_intent
from agents.clarification_agent import clarify_intent
from agents.retrieval_agent import retrieve_products
from agents.reasoning_agent import reason_products
from agents.cart_agent import build_cart
from agents.evaluation_agent import evaluate_cart
from loops.loop_controller import control_loop, reset_loop, get_loop_statistics
from events.event_logger import get_event_statistics, clear_logs


class ShopByIntentionSystem:
    """Main orchestrator for the SHOP-BY-INTENTION system."""
    
    def __init__(self):
        self.intent_state: Optional[Dict[str, Any]] = None
        self.cart_state: Optional[Dict[str, Any]] = None
        self.loop_count = 0
        self.max_loops = 5
    
    def process_user_query(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user query through the complete agentic workflow.
        
        Args:
            user_input: User's natural language query
            
        Returns:
            Complete system result with final cart and reasoning
        """
        print(f"Processing query: {user_input}")
        
        # Reset for new query
        reset_loop()
        clear_logs()
        
        # Initialize state
        self.intent_state = None
        self.cart_state = {"items": [], "total_cost": 0, "is_stable": False}
        self.loop_count = 0
        
        # Main agentic loop
        while self.loop_count < self.max_loops:
            self.loop_count += 1
            print(f"\n--- Loop {self.loop_count} ---")
            
            # Step 1: Intent Parsing
            print("1. Parsing intent...")
            if not self.intent_state:
                self.intent_state = parse_intent(user_input)
                print(f"   Intent: {self.intent_state}")
            
            # Step 2: Clarification (if needed)
            if self.intent_state.get("uncertainty"):
                print("2. Clarifying intent...")
                self.intent_state = clarify_intent(self.intent_state, user_input)
                print(f"   Refined intent: {self.intent_state}")
            
            # Step 3: Product Retrieval
            print("3. Retrieving products...")
            candidates = retrieve_products(self.intent_state)
            print(f"   Found {len(candidates)} candidates")
            
            # Step 4: Reasoning
            print("4. Reasoning about products...")
            reasoning_result = reason_products(self.intent_state, candidates)
            print(f"   Selected {len(reasoning_result['selected_products'])} products")
            
            # Step 5: Cart Building
            print("5. Building cart...")
            self.cart_state = build_cart(reasoning_result, self.intent_state)
            print(f"   Cart total: ${self.cart_state['total_cost']:.2f}")
            
            # Step 6: Evaluation
            print("6. Evaluating cart...")
            evaluation_result = evaluate_cart(self.cart_state, self.intent_state)
            print(f"   Issues found: {len(evaluation_result['issues'])}")
            print(f"   Should continue: {evaluation_result['should_continue']}")
            
            # Step 7: Loop Control
            print("7. Checking loop control...")
            should_continue, next_action, loop_info = control_loop(
                self.intent_state, evaluation_result, self.cart_state
            )
            
            print(f"   Next action: {next_action}")
            print(f"   Loop info: {loop_info}")
            
            # Check termination conditions
            if not should_continue or not evaluation_result['should_continue']:
                print("   Terminating loop...")
                break
            
            # If we need to adjust intent, clear current intent to trigger refinement
            if next_action == "refine_intent":
                self.intent_state = None
                print("   Resetting intent for refinement...")
        
        # Prepare final result
        final_result = {
            "user_query": user_input,
            "final_intent": self.intent_state,
            "final_cart": self.cart_state,
            "loop_count": self.loop_count,
            "loop_statistics": get_loop_statistics(),
            "event_statistics": get_event_statistics()
        }
        
        print(f"\n--- Final Result ---")
        print(f"Loops completed: {self.loop_count}")
        print(f"Final cart items: {len(self.cart_state.get('items', []))}")
        print(f"Total cost: ${self.cart_state.get('total_cost', 0):.2f}")
        
        return final_result
    
    def run_benchmark(self, queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run the system against benchmark queries.
        
        Args:
            queries: List of queries to test (if None, uses default benchmarks)
            
        Returns:
            Benchmark results and metrics
        """
        if queries is None:
            # Load benchmark queries
            try:
                with open("data/benchmark_queries.json", "r") as f:
                    benchmark_data = json.load(f)
                queries = [item["query"] for item in benchmark_data]
            except FileNotFoundError:
                queries = [
                    "I want a gaming laptop under $1500",
                    "I need a cheap camera for photography",
                    "I want a portable coding laptop"
                ]
        
        results = []
        metrics = {
            "total_queries": len(queries),
            "successful_completions": 0,
            "average_loops": 0,
            "average_cart_value": 0
        }
        
        print(f"Running benchmark with {len(queries)} queries...")
        
        for i, query in enumerate(queries):
            print(f"\n--- Benchmark Query {i+1}/{len(queries)} ---")
            result = self.process_user_query(query)
            
            # Calculate metrics
            if result["final_cart"].get("items"):
                metrics["successful_completions"] += 1
                metrics["average_cart_value"] += result["final_cart"]["total_cost"]
            
            results.append(result)
        
        # Calculate averages
        metrics["average_loops"] = sum(r["loop_count"] for r in results) / len(results)
        if metrics["successful_completions"] > 0:
            metrics["average_cart_value"] /= metrics["successful_completions"]
        
        benchmark_result = {
            "metrics": metrics,
            "individual_results": results
        }
        
        print(f"\n--- Benchmark Results ---")
        print(f"Successful completions: {metrics['successful_completions']}/{metrics['total_queries']}")
        print(f"Average loops: {metrics['average_loops']:.1f}")
        print(f"Average cart value: ${metrics['average_cart_value']:.2f}")
        
        return benchmark_result


def main():
    """Main entry point for the SHOP-BY-INTENTION system."""
    print("=== SHOP-BY-INTENTION System ===")
    
    # Create system instance
    system = ShopByIntentionSystem()
    
    # Test with sample queries
    test_queries = [
        "I want a gaming laptop under $1500",
        "I need a cheap camera for photography", 
        "I want a portable coding laptop",
        "Build a home office setup under $1000"
    ]
    
    print("\n1. Running individual tests...")
    for query in test_queries:
        print(f"\n{'='*50}")
        result = system.process_user_query(query)
        
        # Print summary
        cart = result["final_cart"]
        print(f"\nSUMMARY for: {query}")
        print(f"Items: {len(cart.get('items', []))}")
        print(f"Total: ${cart.get('total_cost', 0):.2f}")
        if cart.get("items"):
            for item in cart["items"]:
                print(f"  - {item['name']} (${item['price']})")
    
    print(f"\n{'='*50}")
    print("2. Running benchmark tests...")
    benchmark_result = system.run_benchmark()
    
    # Save results
    with open("data/system_results.json", "w") as f:
        json.dump(benchmark_result, f, indent=2)
    
    print(f"\nResults saved to data/system_results.json")
    print("=== System Complete ===")


if __name__ == "__main__":
    main()