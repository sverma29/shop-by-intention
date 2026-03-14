"""
Cart Agent for SHOP-BY-INTENTION System

Constructs and updates the shopping cart based on reasoning results.
"""

from typing import Dict, Any, List, Optional
from core.events.event_model import CartState, AgenticEvent, EventType
from core.events.event_logger import log_event


class CartAgent:
    """Constructs and updates the shopping cart."""
    
    def __init__(self):
        self.cart = CartState()
        self.compatibility_rules = {
            "laptop": ["mouse", "keyboard", "monitor"],
            "monitor": ["laptop", "keyboard", "mouse"],
            "keyboard": ["laptop", "monitor"],
            "mouse": ["laptop", "monitor"],
            "chair": ["desk"],
            "desk": ["chair", "monitor", "keyboard", "mouse"]
        }
    
    def build_cart(self, reasoning_result: Dict[str, Any], intent_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build or update the shopping cart.
        
        Args:
            reasoning_result: Result from reasoning agent
            intent_state: User's structured intent
            
        Returns:
            Updated cart state
        """
        # Ensure the cart starts clean to avoid duplicate accumulation in evaluation loops
        self.cart = CartState()

        selected_products = reasoning_result.get("selected_products", [])
        
        if not selected_products:
            return self.cart.to_dict()
        
        # Determine cart strategy based on intent
        cart_strategy = self._determine_cart_strategy(intent_state)
        
        if cart_strategy == "single_item":
            # Replace cart with single best item
            self._replace_cart_with_single_item(selected_products[0])
        elif cart_strategy == "setup":
            # Add complementary items to setup
            self._build_setup_cart(selected_products, intent_state)
        else:
            # Add top items
            self._add_top_items(selected_products)
        
        # Check compatibility
        compatibility_issues = self._check_compatibility()
        
        # Log cart update
        cart_event = AgenticEvent.create(
            event_type=EventType.CART_UPDATED,
            agent="CartAgent",
            input_state={
                "reasoning_result": reasoning_result,
                "intent": intent_state
            },
            decision={
                "cart_strategy": cart_strategy,
                "items_added": len(selected_products),
                "compatibility_issues": len(compatibility_issues)
            },
            output_state=self.cart.to_dict(),
            confidence=self._calculate_cart_confidence(compatibility_issues)
        )
        log_event(cart_event)
        
        # Check if cart is stable
        if self._is_cart_stable(intent_state):
            stable_event = AgenticEvent.create(
                event_type=EventType.CART_STABLE,
                agent="CartAgent",
                input_state=self.cart.to_dict(),
                decision={
                    "stability_reason": "requirements_met",
                    "total_cost": self.cart.total_cost
                },
                output_state={**self.cart.to_dict(), "stable": True},
                confidence=0.9
            )
            log_event(stable_event)
        
        return self.cart.to_dict()
    
    def _determine_cart_strategy(self, intent_state: Dict[str, Any]) -> str:
        """Determine the cart building strategy."""
        category = intent_state.get("category")
        purpose = intent_state.get("purpose")
        
        # Setup intent
        if category == "office setup" or purpose == "home office":
            return "setup"
        
        # Default to multiple items
        return "multiple_items"
    
    def _replace_cart_with_single_item(self, product: Dict[str, Any]):
        """Replace cart with a single item."""
        self.cart = CartState()
        self.cart.add_item(product)
    
    def _build_setup_cart(self, selected_products: List[Dict[str, Any]], intent_state: Dict[str, Any]):
        """Build a complete setup cart."""
        # Start with main item
        if selected_products:
            self.cart.add_item(selected_products[0])
        
        # Add complementary items based on intent
        budget = intent_state.get("budget", 0)
        remaining_budget = budget - self.cart.total_cost
        
        # Add peripherals if within budget
        complementary_items = self._get_complementary_items(selected_products[0] if selected_products else {}, remaining_budget)
        
        for item in complementary_items:
            if self.cart.total_cost + item.get("price", 0) <= budget:
                self.cart.add_item(item)
    
    def _add_top_items(self, selected_products: List[Dict[str, Any]]):
        """Add top items to cart."""
        for product in selected_products[:3]:  # Add top 3
            self.cart.add_item(product)
    
    def _get_complementary_items(self, main_product: Dict[str, Any], budget: float) -> List[Dict[str, Any]]:
        """Get complementary items for a setup."""
        from ..data.product_catalog import products  # Import catalog
        
        category = main_product.get("category")
        compatible_categories = self.compatibility_rules.get(category, [])
        
        complementary = []
        for product in products:
            if (product["category"] in compatible_categories and 
                product["price"] <= budget and
                product["id"] != main_product.get("id")):
                complementary.append(product)
        
        # Sort by relevance
        complementary.sort(key=lambda x: x["price"])
        return complementary[:3]  # Return top 3
    
    def _check_compatibility(self) -> List[Dict[str, Any]]:
        """Check for compatibility issues in the cart."""
        issues = []
        categories = [item.get("category") for item in self.cart.items]
        
        # Check for missing essential items
        if "laptop" in categories and "mouse" not in categories:
            issues.append({
                "type": "missing_peripheral",
                "missing": "mouse",
                "severity": "low"
            })
        
        if "laptop" in categories and "keyboard" not in categories:
            issues.append({
                "type": "missing_peripheral", 
                "missing": "keyboard",
                "severity": "low"
            })
        
        # Check for budget overruns
        if self.cart.total_cost > 0:  # Only check if we have a budget
            pass  # Budget checking handled elsewhere
        
        return issues
    
    def _is_cart_stable(self, intent_state: Dict[str, Any]) -> bool:
        """Determine if the cart is stable."""
        budget = intent_state.get("budget")
        
        # If no budget specified, consider stable if we have items
        if not budget:
            return len(self.cart.items) > 0
        
        # Check if within budget
        if self.cart.total_cost > budget:
            return False
        
        # Check if we have the right category
        category = intent_state.get("category")
        if category and category not in [item.get("category") for item in self.cart.items]:
            return False
        
        # Consider stable if requirements are met
        return True
    
    def _calculate_cart_confidence(self, compatibility_issues: List[Dict[str, Any]]) -> float:
        """Calculate confidence in the cart."""
        base_confidence = 0.8
        penalty = len(compatibility_issues) * 0.1
        
        return max(0.1, base_confidence - penalty)
    
    def clear_cart(self):
        """Clear the shopping cart."""
        self.cart = CartState()
        
        # Log cart clearing
        clear_event = AgenticEvent.create(
            event_type=EventType.CART_UPDATED,
            agent="CartAgent",
            input_state={"previous_cart": self.cart.to_dict()},
            decision={"action": "cleared"},
            output_state=self.cart.to_dict(),
            confidence=0.5
        )
        log_event(clear_event)


# Global cart agent instance
cart_agent = CartAgent()


def build_cart(reasoning_result: Dict[str, Any], intent_state: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to build cart using the global agent."""
    return cart_agent.build_cart(reasoning_result, intent_state)


def clear_cart():
    """Convenience function to clear cart using the global agent."""
    cart_agent.clear_cart()