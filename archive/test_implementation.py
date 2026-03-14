"""
Test script to validate the SHOP-BY-INTENTION implementation.

This script checks that all components can be imported and basic functionality works.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from events.event_model import IntentState, AgenticEvent, EventType
        print("✓ Event model imports successful")
    except ImportError as e:
        print(f"✗ Event model import failed: {e}")
        return False
    
    try:
        from events.event_logger import EventLogger, log_event
        print("✓ Event logger imports successful")
    except ImportError as e:
        print(f"✗ Event logger import failed: {e}")
        return False
    
    try:
        from agents.intent_agent import IntentAgent, parse_intent
        print("✓ Intent agent imports successful")
    except ImportError as e:
        print(f"✗ Intent agent import failed: {e}")
        return False
    
    try:
        from agents.clarification_agent import ClarificationAgent, clarify_intent
        print("✓ Clarification agent imports successful")
    except ImportError as e:
        print(f"✗ Clarification agent import failed: {e}")
        return False
    
    try:
        from agents.retrieval_agent import RetrievalAgent, retrieve_products
        print("✓ Retrieval agent imports successful")
    except ImportError as e:
        print(f"✗ Retrieval agent import failed: {e}")
        return False
    
    try:
        from agents.reasoning_agent import ReasoningAgent, reason_products
        print("✓ Reasoning agent imports successful")
    except ImportError as e:
        print(f"✗ Reasoning agent import failed: {e}")
        return False
    
    try:
        from agents.cart_agent import CartAgent, build_cart
        print("✓ Cart agent imports successful")
    except ImportError as e:
        print(f"✗ Cart agent import failed: {e}")
        return False
    
    try:
        from agents.evaluation_agent import EvaluationAgent, evaluate_cart
        print("✓ Evaluation agent imports successful")
    except ImportError as e:
        print(f"✗ Evaluation agent import failed: {e}")
        return False
    
    try:
        from loops.loop_controller import LoopController, control_loop
        print("✓ Loop controller imports successful")
    except ImportError as e:
        print(f"✗ Loop controller import failed: {e}")
        return False
    
    try:
        from main import ShopByIntentionSystem
        print("✓ Main system imports successful")
    except ImportError as e:
        print(f"✗ Main system import failed: {e}")
        return False
    
    return True

def test_data_files():
    """Test that data files exist and are valid."""
    print("\nTesting data files...")
    
    # Test product catalog
    try:
        with open("data/product_catalog.json", "r") as f:
            import json
            catalog = json.load(f)
            if catalog and isinstance(catalog, list) and len(catalog) > 0:
                print(f"✓ Product catalog loaded: {len(catalog)} products")
            else:
                print("✗ Product catalog is empty or invalid")
                return False
    except Exception as e:
        print(f"✗ Product catalog load failed: {e}")
        return False
    
    # Test benchmark queries
    try:
        with open("data/benchmark_queries.json", "r") as f:
            queries = json.load(f)
            if queries and isinstance(queries, list) and len(queries) > 0:
                print(f"✓ Benchmark queries loaded: {len(queries)} queries")
            else:
                print("✗ Benchmark queries are empty or invalid")
                return False
    except Exception as e:
        print(f"✗ Benchmark queries load failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of key components."""
    print("\nTesting basic functionality...")
    
    try:
        from events.event_model import IntentState, EventType, AgenticEvent
        
        # Test IntentState
        intent = IntentState(
            category="laptop",
            purpose="gaming",
            budget=1500,
            preferences=["lightweight"],
            uncertainty=None
        )
        intent_dict = intent.to_dict()
        if intent_dict["category"] == "laptop" and intent_dict["budget"] == 1500:
            print("✓ IntentState functionality works")
        else:
            print("✗ IntentState functionality failed")
            return False
        
        # Test AgenticEvent
        event = AgenticEvent.create(
            event_type=EventType.INTENT_PARSED,
            agent="TestAgent",
            input_state={"test": "data"},
            decision={"test": "decision"},
            output_state={"test": "output"},
            confidence=0.9
        )
        if event.event_type == EventType.INTENT_PARSED and event.agent == "TestAgent":
            print("✓ AgenticEvent functionality works")
        else:
            print("✗ AgenticEvent functionality failed")
            return False
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False
    
    return True

def test_agent_functionality():
    """Test that agents can be instantiated and have expected methods."""
    print("\nTesting agent functionality...")
    
    try:
        from agents.intent_agent import IntentAgent
        from agents.clarification_agent import ClarificationAgent
        from agents.retrieval_agent import RetrievalAgent
        from agents.reasoning_agent import ReasoningAgent
        from agents.cart_agent import CartAgent
        from agents.evaluation_agent import EvaluationAgent
        
        # Test agent instantiation
        intent_agent = IntentAgent()
        clarification_agent = ClarificationAgent()
        retrieval_agent = RetrievalAgent()
        reasoning_agent = ReasoningAgent()
        cart_agent = CartAgent()
        evaluation_agent = EvaluationAgent()
        
        print("✓ All agents can be instantiated")
        
        # Test that agents have expected methods
        if hasattr(intent_agent, 'parse_intent') and callable(getattr(intent_agent, 'parse_intent')):
            print("✓ IntentAgent has parse_intent method")
        else:
            print("✗ IntentAgent missing parse_intent method")
            return False
        
        if hasattr(retrieval_agent, 'retrieve_products') and callable(getattr(retrieval_agent, 'retrieve_products')):
            print("✓ RetrievalAgent has retrieve_products method")
        else:
            print("✗ RetrievalAgent missing retrieve_products method")
            return False
        
        if hasattr(reasoning_agent, 'reason_products') and callable(getattr(reasoning_agent, 'reason_products')):
            print("✓ ReasoningAgent has reason_products method")
        else:
            print("✗ ReasoningAgent missing reason_products method")
            return False
        
    except Exception as e:
        print(f"✗ Agent functionality test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=== SHOP-BY-INTENTION Implementation Test ===\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Data File Tests", test_data_files),
        ("Basic Functionality Tests", test_basic_functionality),
        ("Agent Functionality Tests", test_agent_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name}...")
        print('='*50)
        
        if test_func():
            print(f"✓ {test_name} PASSED")
            passed += 1
        else:
            print(f"✗ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! Implementation appears to be working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)