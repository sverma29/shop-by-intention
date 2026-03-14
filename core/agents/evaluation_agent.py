"""
Evaluation Agent for SHOP-BY-INTENTION System

Performs online evaluation during system execution.
"""

from typing import Dict, Any, List, Optional
from core.events.event_model import AgenticEvent, EventType
from core.events.event_logger import log_event


class EvaluationAgent:
    """Performs online evaluation during execution."""
    
    def __init__(self):
        self.evaluation_rules = {
            "budget_check": self._check_budget_compliance,
            "compatibility_check": self._check_item_compatibility,
            "completeness_check": self._check_cart_completeness,
            "intent_alignment_check": self._check_intent_alignment
        }
    
    def evaluate_cart(self, cart_state: Dict[str, Any], intent_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the current cart state.
        
        Args:
            cart_state: Current cart state
            intent_state: User's structured intent
            
        Returns:
            Evaluation result with recommendations
        """
        evaluations = {}
        issues = []
        recommendations = []
        
        # Run all evaluation checks
        for check_name, check_func in self.evaluation_rules.items():
            result = check_func(cart_state, intent_state)
            evaluations[check_name] = result
            
            if not result["passed"]:
                issues.extend(result.get("issues", []))
                recommendations.extend(result.get("recommendations", []))
        
        # Determine overall evaluation
        overall_pass = len(issues) == 0
        should_continue = self._should_continue_planning(issues, cart_state, intent_state)
        
        # Log evaluation result
        evaluation_event = AgenticEvent.create(
            event_type=EventType.LOOP_TRIGGERED if should_continue else EventType.TASK_TERMINATED,
            agent="EvaluationAgent",
            input_state={
                "cart": cart_state,
                "intent": intent_state
            },
            decision={
                "overall_pass": overall_pass,
                "issues_found": len(issues),
                "should_continue": should_continue,
                "recommendations_count": len(recommendations)
            },
            output_state={
                "evaluation_summary": evaluations,
                "issues": issues,
                "recommendations": recommendations
            },
            confidence=self._calculate_evaluation_confidence(evaluations)
        )
        log_event(evaluation_event)
        
        # Log goal conflicts if any
        if issues:
            conflict_event = AgenticEvent.create(
                event_type=EventType.GOAL_CONFLICT_DETECTED,
                agent="EvaluationAgent",
                input_state={"issues": issues},
                decision={
                    "conflict_types": [issue.get("type") for issue in issues],
                    "severity": "high" if len(issues) > 2 else "medium"
                },
                output_state={"recommendations": recommendations},
                confidence=0.8
            )
            log_event(conflict_event)
        
        return {
            "evaluations": evaluations,
            "issues": issues,
            "recommendations": recommendations,
            "should_continue": should_continue,
            "overall_pass": overall_pass,
            "confidence": self._calculate_evaluation_confidence(evaluations)
        }
    
    def _check_budget_compliance(self, cart_state: Dict[str, Any], intent_state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if cart complies with budget."""
        budget = intent_state.get("budget")
        total_cost = cart_state.get("total_cost", 0)
        
        if not budget:
            return {
                "passed": True,
                "score": 1.0,
                "issues": [],
                "recommendations": []
            }
        
        overage = total_cost - budget
        overage_percentage = (overage / budget) * 100 if budget > 0 else 0
        
        if overage <= 0:
            return {
                "passed": True,
                "score": 1.0,
                "issues": [],
                "recommendations": []
            }
        else:
            issue = {
                "type": "budget_exceeded",
                "description": f"Cart exceeds budget by ${overage:.2f} ({overage_percentage:.1f}%)",
                "severity": "high" if overage_percentage > 20 else "medium"
            }
            
            recommendation = {
                "type": "budget_adjustment",
                "description": f"Remove items totaling at least ${overage:.2f} or find cheaper alternatives",
                "priority": "high"
            }
            
            return {
                "passed": False,
                "score": max(0, 1.0 - (overage_percentage / 100)),
                "issues": [issue],
                "recommendations": [recommendation]
            }
    
    def _check_item_compatibility(self, cart_state: Dict[str, Any], intent_state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if items in cart are compatible."""
        items = cart_state.get("items", [])
        issues = []
        recommendations = []
        
        # Check for incompatible combinations
        categories = [item.get("category") for item in items]
        
        # Missing essential peripherals for laptops
        if "laptop" in categories:
            if "mouse" not in categories:
                issues.append({
                    "type": "missing_peripheral",
                    "description": "Laptop detected but no mouse included",
                    "severity": "low"
                })
                recommendations.append({
                    "type": "add_peripheral",
                    "description": "Consider adding a mouse for better usability",
                    "priority": "low"
                })
            
            if "keyboard" not in categories:
                issues.append({
                    "type": "missing_peripheral",
                    "description": "Laptop detected but no external keyboard included",
                    "severity": "low"
                })
                recommendations.append({
                    "type": "add_peripheral",
                    "description": "Consider adding an external keyboard for extended use",
                    "priority": "low"
                })
        
        # Chair without desk
        if "chair" in categories and "desk" not in categories:
            issues.append({
                "type": "incomplete_setup",
                "description": "Chair included without desk",
                "severity": "medium"
            })
            recommendations.append({
                "type": "add_complementary",
                "description": "Consider adding a desk to complete the setup",
                "priority": "medium"
            })
        
        return {
            "passed": len(issues) == 0,
            "score": max(0, 1.0 - (len(issues) * 0.2)),
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _check_cart_completeness(self, cart_state: Dict[str, Any], intent_state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if cart is complete based on intent."""
        items = cart_state.get("items", [])
        category = intent_state.get("category")
        purpose = intent_state.get("purpose")
        
        issues = []
        recommendations = []
        
        # Check if we have the right main category
        if category and category not in [item.get("category") for item in items]:
            issues.append({
                "type": "wrong_category",
                "description": f"Expected {category} but cart contains different items",
                "severity": "high"
            })
            recommendations.append({
                "type": "category_correction",
                "description": f"Add items from {category} category",
                "priority": "high"
            })
        
        # Check for setup completeness
        if category == "office setup" or purpose == "home office":
            required_items = {"laptop", "monitor", "keyboard", "mouse", "chair", "desk"}
            cart_categories = set(item.get("category") for item in items)
            missing = required_items - cart_categories
            
            if missing:
                issues.append({
                    "type": "incomplete_setup",
                    "description": f"Missing items for office setup: {', '.join(missing)}",
                    "severity": "medium"
                })
                recommendations.append({
                    "type": "complete_setup",
                    "description": f"Add missing items: {', '.join(missing)}",
                    "priority": "medium"
                })
        
        return {
            "passed": len(issues) == 0,
            "score": max(0, 1.0 - (len(issues) * 0.3)),
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _check_intent_alignment(self, cart_state: Dict[str, Any], intent_state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if cart aligns with user intent."""
        items = cart_state.get("items", [])
        preferences = intent_state.get("preferences", [])
        
        issues = []
        recommendations = []
        
        # Check preference alignment
        cart_features = []
        for item in items:
            cart_features.extend(item.get("features", []))
        
        missing_preferences = []
        for preference in preferences:
            if preference not in cart_features:
                missing_preferences.append(preference)
        
        if missing_preferences:
            issues.append({
                "type": "preference_mismatch",
                "description": f"Missing preferred features: {', '.join(missing_preferences)}",
                "severity": "medium"
            })
            recommendations.append({
                "type": "preference_alignment",
                "description": f"Consider items with features: {', '.join(missing_preferences)}",
                "priority": "medium"
            })
        
        return {
            "passed": len(issues) == 0,
            "score": max(0, 1.0 - (len(missing_preferences) * 0.2)),
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _should_continue_planning(self, issues: List[Dict[str, Any]], cart_state: Dict[str, Any], intent_state: Dict[str, Any]) -> bool:
        """Determine if planning should continue."""
        # Always continue if there are high-severity issues
        high_severity_issues = [issue for issue in issues if issue.get("severity") == "high"]
        if high_severity_issues:
            return True
        
        # Continue if budget is exceeded
        budget_issues = [issue for issue in issues if issue.get("type") == "budget_exceeded"]
        if budget_issues:
            return True
        
        # Continue if wrong category
        category_issues = [issue for issue in issues if issue.get("type") == "wrong_category"]
        if category_issues:
            return True
        
        # Continue if cart is empty and we have intent
        if not cart_state.get("items") and intent_state.get("category"):
            return True
        
        # Otherwise, terminate
        return False
    
    def _calculate_evaluation_confidence(self, evaluations: Dict[str, Any]) -> float:
        """Calculate overall evaluation confidence."""
        scores = [eval.get("score", 0) for eval in evaluations.values()]
        if not scores:
            return 0.5
        
        return sum(scores) / len(scores)


# Global evaluation agent instance
evaluation_agent = EvaluationAgent()


def evaluate_cart(cart_state: Dict[str, Any], intent_state: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to evaluate cart using the global agent."""
    return evaluation_agent.evaluate_cart(cart_state, intent_state)