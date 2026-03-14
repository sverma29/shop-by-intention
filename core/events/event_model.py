"""
Event Model for SHOP-BY-INTENTION System

Defines the core event schema and types used throughout the agentic system.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class EventType(Enum):
    """Core event types in the agentic system."""
    INTENT_PARSED = "INTENT_PARSED"
    INTENT_UNCERTAIN = "INTENT_UNCERTAIN"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    INTENT_REFINED = "INTENT_REFINED"
    RETRIEVAL_STRATEGY_SELECTED = "RETRIEVAL_STRATEGY_SELECTED"
    CONTEXT_ACCEPTED = "CONTEXT_ACCEPTED"
    CONTEXT_REJECTED = "CONTEXT_REJECTED"
    REASONING_PATH_CHOSEN = "REASONING_PATH_CHOSEN"
    GOAL_CONFLICT_DETECTED = "GOAL_CONFLICT_DETECTED"
    CART_UPDATED = "CART_UPDATED"
    CART_STABLE = "CART_STABLE"
    LOOP_TRIGGERED = "LOOP_TRIGGERED"
    TASK_TERMINATED = "TASK_TERMINATED"


@dataclass
class AgenticEvent:
    """Structured event for the agentic AI system."""
    event_id: str
    timestamp: str
    event_type: EventType
    agent: str
    input_state: Dict[str, Any]
    decision: Dict[str, Any]
    output_state: Dict[str, Any]
    confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary format."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "agent": self.agent,
            "input_state": self.input_state,
            "decision": self.decision,
            "output_state": self.output_state,
            "confidence": self.confidence
        }
    
    @classmethod
    def create(
        cls,
        event_type: EventType,
        agent: str,
        input_state: Dict[str, Any],
        decision: Dict[str, Any],
        output_state: Dict[str, Any],
        confidence: Optional[float] = None
    ) -> 'AgenticEvent':
        """Create a new agentic event."""
        return cls(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            agent=agent,
            input_state=input_state,
            decision=decision,
            output_state=output_state,
            confidence=confidence
        )


class IntentState:
    """Represents the structured intent state."""
    def __init__(
        self,
        category: Optional[str] = None,
        purpose: Optional[str] = None,
        budget: Optional[float] = None,
        preferences: Optional[list] = None,
        uncertainty: Optional[str] = None
    ):
        self.category = category
        self.purpose = purpose
        self.budget = budget
        self.preferences = preferences or []
        self.uncertainty = uncertainty
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert intent state to dictionary."""
        return {
            "category": self.category,
            "purpose": self.purpose,
            "budget": self.budget,
            "preferences": self.preferences,
            "uncertainty": self.uncertainty
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntentState':
        """Create intent state from dictionary."""
        return cls(
            category=data.get("category"),
            purpose=data.get("purpose"),
            budget=data.get("budget"),
            preferences=data.get("preferences", []),
            uncertainty=data.get("uncertainty")
        )


class CartState:
    """Represents the shopping cart state."""
    def __init__(self):
        self.items: list = []
        self.total_cost: float = 0.0
        self.is_stable: bool = False
    
    def add_item(self, item: Dict[str, Any]):
        """Add an item to the cart."""
        self.items.append(item)
        self.total_cost += item.get("price", 0)
        self.is_stable = False
    
    def remove_item(self, item_id: str):
        """Remove an item from the cart."""
        self.items = [item for item in self.items if item.get("id") != item_id]
        self.total_cost = sum(item.get("price", 0) for item in self.items)
        self.is_stable = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cart state to dictionary."""
        return {
            "items": self.items,
            "total_cost": self.total_cost,
            "is_stable": self.is_stable
        }