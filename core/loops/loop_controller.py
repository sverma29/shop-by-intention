"""
Loop Controller for SHOP-BY-INTENTION System

Controls agentic loops and determines when to continue or terminate.
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from core.events.event_model import AgenticEvent, EventType
from core.events.event_logger import log_event


class LoopState(Enum):
    """Possible states of the agentic loop."""
    INTENT_REFINEMENT = "intent_refinement"
    RETRIEVAL_REASONING = "retrieval_reasoning"
    CART_OPTIMIZATION = "cart_optimization"
    TERMINATED = "terminated"


class LoopController:
    """Controls the agentic loops in the system."""
    
    def __init__(self):
        self.max_loops = 5
        self.current_loop = 0
        self.loop_history: List[Dict[str, Any]] = []
        self.state = LoopState.INTENT_REFINEMENT
    
    def control_loop(self, 
                    intent_state: Dict[str, Any],
                    evaluation_result: Dict[str, Any],
                    cart_state: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Control the agentic loop based on evaluation results.
        
        Args:
            intent_state: Current intent state
            evaluation_result: Result from evaluation agent
            cart_state: Current cart state
            
        Returns:
            Tuple of (should_continue, next_action, loop_info)
        """
        self.current_loop += 1
        
        # Check termination conditions
        if self._should_terminate(evaluation_result, cart_state):
            self.state = LoopState.TERMINATED
            return False, "terminate", self._get_loop_info()
        
        # Check if we've exceeded max loops
        if self.current_loop >= self.max_loops:
            self.state = LoopState.TERMINATED
            return False, "max_loops_exceeded", self._get_loop_info()
        
        # Determine next action based on evaluation
        next_action = self._determine_next_action(evaluation_result, intent_state)
        
        # Update loop state
        self._update_loop_state(next_action)
        
        # Log loop decision
        loop_event = AgenticEvent.create(
            event_type=EventType.LOOP_TRIGGERED,
            agent="LoopController",
            input_state={
                "current_loop": self.current_loop,
                "evaluation_result": evaluation_result,
                "cart_state": cart_state
            },
            decision={
                "next_action": next_action,
                "loop_state": self.state.value,
                "should_continue": True
            },
            output_state=self._get_loop_info(),
            confidence=0.8
        )
        log_event(loop_event)
        
        return True, next_action, self._get_loop_info()
    
    def _should_terminate(self, evaluation_result: Dict[str, Any], cart_state: Dict[str, Any]) -> bool:
        """Determine if the loop should terminate."""
        # Terminate if evaluation says to stop
        if not evaluation_result.get("should_continue", True):
            return True
        
        # Terminate if cart is stable
        if cart_state.get("is_stable", False):
            return True
        
        # Terminate if we have a good cart and no major issues
        issues = evaluation_result.get("issues", [])
        major_issues = [issue for issue in issues if issue.get("severity") in ["high", "critical"]]
        
        if not major_issues and len(cart_state.get("items", [])) > 0:
            return True
        
        return False
    
    def _determine_next_action(self, evaluation_result: Dict[str, Any], intent_state: Dict[str, Any]) -> str:
        """Determine the next action based on evaluation."""
        issues = evaluation_result.get("issues", [])
        
        # High priority issues take precedence
        high_issues = [issue for issue in issues if issue.get("severity") == "high"]
        
        if high_issues:
            for issue in high_issues:
                if issue.get("type") == "wrong_category":
                    return "refine_intent"
                elif issue.get("type") == "budget_exceeded":
                    return "adjust_retrieval"
                elif issue.get("type") == "missing_category":
                    return "expand_retrieval"
        
        # Medium priority issues
        medium_issues = [issue for issue in issues if issue.get("severity") == "medium"]
        
        if medium_issues:
            for issue in medium_issues:
                if issue.get("type") in ["preference_mismatch", "incomplete_setup"]:
                    return "adjust_retrieval"
                elif issue.get("type") == "incompatible_items":
                    return "replan_cart"
        
        # Low priority issues
        low_issues = [issue for issue in issues if issue.get("severity") == "low"]
        
        if low_issues:
            return "replan_cart"
        
        # If no issues, but cart is not stable, optimize cart
        if not intent_state.get("uncertainty") and not cart_state.get("is_stable"):
            return "optimize_cart"
        
        # Default: continue with current flow
        return "continue_flow"
    
    def _update_loop_state(self, next_action: str):
        """Update the loop state based on next action."""
        if next_action in ["refine_intent", "clarify_intent"]:
            self.state = LoopState.INTENT_REFINEMENT
        elif next_action in ["adjust_retrieval", "expand_retrieval", "retrieval"]:
            self.state = LoopState.RETRIEVAL_REASONING
        elif next_action in ["replan_cart", "optimize_cart"]:
            self.state = LoopState.CART_OPTIMIZATION
        else:
            # Maintain current state for continue_flow
            pass
    
    def _get_loop_info(self) -> Dict[str, Any]:
        """Get current loop information."""
        return {
            "current_loop": self.current_loop,
            "max_loops": self.max_loops,
            "state": self.state.value,
            "history": self.loop_history[-3:],  # Last 3 loops
            "progress": f"{self.current_loop}/{self.max_loops}"
        }
    
    def reset(self):
        """Reset the loop controller."""
        self.current_loop = 0
        self.loop_history = []
        self.state = LoopState.INTENT_REFINEMENT
        
        # Log reset
        reset_event = AgenticEvent.create(
            event_type=EventType.INTENT_PARSED,  # Using this as reset event
            agent="LoopController",
            input_state={},
            decision={"action": "reset"},
            output_state=self._get_loop_info(),
            confidence=1.0
        )
        log_event(reset_event)
    
    def get_loop_statistics(self) -> Dict[str, Any]:
        """Get statistics about the loop execution."""
        return {
            "total_loops": self.current_loop,
            "max_loops": self.max_loops,
            "current_state": self.state.value,
            "history_length": len(self.loop_history),
            "completion_rate": self.current_loop / self.max_loops if self.max_loops > 0 else 0
        }


# Global loop controller instance
loop_controller = LoopController()


def control_loop(intent_state: Dict[str, Any], 
                evaluation_result: Dict[str, Any], 
                cart_state: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Convenience function to control loop using the global controller."""
    return loop_controller.control_loop(intent_state, evaluation_result, cart_state)


def reset_loop():
    """Convenience function to reset loop using the global controller."""
    loop_controller.reset()


def get_loop_statistics() -> Dict[str, Any]:
    """Convenience function to get loop statistics using the global controller."""
    return loop_controller.get_loop_statistics()