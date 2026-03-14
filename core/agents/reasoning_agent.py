"""
AI-Enhanced Reasoning Agent for SHOP-BY-INTENTION System

Uses LLM for intelligent product comparison, trade-off analysis, and recommendation generation.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from core.ai.model_service import get_ai_service
from core.events.event_model import AgenticEvent, EventType
from core.events.event_logger import log_event
from core.config.groq_config import get_config

# Configure logging
logger = logging.getLogger(__name__)


class AIEnhancedReasoningAgent:
    """Enhanced Reasoning Agent using LLM for intelligent product analysis."""
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.config = get_config()
        self.reasoning_prompt = self._build_reasoning_prompt()
    
    def _build_reasoning_prompt(self) -> str:
        """Build the prompt template for product reasoning."""
        return """
You are an expert shopping advisor. Analyze these products and provide recommendations.

User Intent:
{intent_summary}

Products to analyze:
{product_list}

Instructions:
1. Compare products based on user intent (category, purpose, budget, preferences)
2. Identify trade-offs between products (performance vs budget, features vs portability, etc.)
3. Consider value for money and user priorities
4. Provide a ranked recommendation with detailed reasoning
5. Explain any trade-offs the user should consider

Return JSON format:
{{
  "recommendations": [
    {{
      "product_id": "string",
      "rank": number,
      "score": 1-10,
      "reasoning": "detailed explanation",
      "pros": ["list", "of", "pros"],
      "cons": ["list", "of", "cons"],
      "trade_offs": ["list", "of", "trade-offs"]
    }}
  ],
  "trade_off_analysis": "summary of key trade-offs",
  "best_value": "product_id of best value",
  "overall_confidence": 0.0 to 1.0
}}
"""
    
    def reason_products(self, intent_state: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reason about products using LLM analysis.
        
        Args:
            intent_state: User's structured intent
            candidates: List of candidate products
            
        Returns:
            LLM-powered reasoning result with detailed explanations
        """
        logger.info(f"AI Reasoning Agent analyzing {len(candidates)} candidates")
        
        if not candidates:
            return {
                "selected_products": [],
                "reasoning": "No candidates available for analysis",
                "trade_offs": [],
                "confidence": 0.0,
                "llm_analysis": None
            }
        
        try:
            # Create intent summary
            intent_summary = self._create_intent_summary(intent_state)
            
            # Create product list for LLM
            product_list = self._format_products_for_llm(candidates)
            
            # Build prompt
            prompt = self.reasoning_prompt.format(
                intent_summary=intent_summary,
                product_list=product_list
            )
            
            # Get LLM analysis
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.6,  # Slightly higher for creative analysis
                max_tokens=1500
            )
            
            # Parse LLM response
            reasoning_result = self._parse_llm_reasoning_response(ai_response.content, candidates)
            
            # Select top products based on LLM ranking
            selected_products = self._select_products_from_llm(reasoning_result, candidates)
            
            # Log reasoning decision
            self._log_reasoning_event(intent_state, candidates, reasoning_result, ai_response)
            
            logger.info(f"AI Reasoning completed with {len(selected_products)} selected products")
            return {
                "selected_products": selected_products,
                "reasoning": reasoning_result,
                "trade_offs": reasoning_result.get("trade_offs", []),
                "confidence": ai_response.confidence,
                "llm_analysis": reasoning_result
            }
            
        except Exception as e:
            logger.error(f"AI Reasoning failed: {e}")
            # Return empty result if LLM fails
            return {
                "selected_products": [],
                "reasoning": f"Reasoning failed: {e}",
                "trade_offs": [],
                "confidence": 0.0,
                "llm_analysis": None
            }
    
    def _create_intent_summary(self, intent: Dict[str, Any]) -> str:
        """Create a summary of user intent for LLM."""
        parts = []
        
        if intent.get("category"):
            parts.append(f"Category: {intent['category']}")
        if intent.get("purpose"):
            parts.append(f"Purpose: {intent['purpose']}")
        if intent.get("budget"):
            parts.append(f"Budget: ${intent['budget']}")
        if intent.get("preferences"):
            parts.append(f"Preferences: {', '.join(intent['preferences'])}")
        
        return " | ".join(parts) if parts else "General shopping intent"
    
    def _format_products_for_llm(self, products: List[Dict[str, Any]]) -> str:
        """Format products for LLM analysis."""
        formatted_products = []
        
        for i, product in enumerate(products, 1):
            features = ", ".join(product.get("features", []))
            purpose_list = ", ".join(product.get("purpose", []))
            
            product_text = f"""
Product {i}:
ID: {product['id']}
Name: {product['name']}
Brand: {product['brand']}
Category: {product['category']}
Price: ${product['price']}
Purpose: {purpose_list}
Features: {features}
"""
            formatted_products.append(product_text)
        
        return "\n".join(formatted_products)
    
    def _parse_llm_reasoning_response(self, response_text: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse LLM reasoning response."""
        try:
            # Strip markdown formatting
            cleaned_response = response_text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
                
            # Try to extract JSON using regex
            import re
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback: create basic structure
            return {
                "recommendations": [],
                "trade_off_analysis": "Unable to parse detailed analysis",
                "best_value": None,
                "overall_confidence": 0.5
            }
            
        except Exception as e:
            logger.error(f"Failed to parse LLM reasoning response: {e}")
            return {
                "recommendations": [],
                "trade_off_analysis": "Error in analysis",
                "best_value": None,
                "overall_confidence": 0.0
            }
    
    def _select_products_from_llm(self, reasoning_result: Dict[str, Any], candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select products based on LLM recommendations."""
        recommendations = reasoning_result.get("recommendations", [])
        
        if not recommendations:
            # Fallback to first few candidates
            return candidates[:3]
        
        # Get product IDs from recommendations safely handling different JSON formats
        selected_ids = []
        for rec in recommendations:
            if isinstance(rec, dict):
                # The LLM is instructed to use product_id, but it may use 'id' instead.
                product_id = rec.get("product_id") or rec.get("id")
                if product_id:
                    selected_ids.append(product_id)
        
        # Find corresponding products
        selected_products = []
        for product_id in selected_ids:
            for product in candidates:
                if product["id"] == product_id:
                    selected_products.append(product)
                    break
        
        return selected_products
    
    def _log_reasoning_event(self, intent_state: Dict[str, Any], candidates: List[Dict[str, Any]], reasoning_result: Dict[str, Any], ai_response):
        """Log the reasoning event."""
        event = AgenticEvent.create(
            event_type=EventType.REASONING_PATH_CHOSEN,
            agent="AIEnhancedReasoningAgent",
            input_state={
                "intent": intent_state,
                "candidates_count": len(candidates)
            },
            decision={
                "reasoning_method": "llm_analysis",
                "llm_model": ai_response.model,
                "llm_confidence": ai_response.confidence,
                "recommendations_count": len(reasoning_result.get("recommendations", []))
            },
            output_state={
                "selected_products": [p.get("product_id") or p.get("id") for p in reasoning_result.get("recommendations", []) if isinstance(p, dict)],
                "trade_off_analysis": reasoning_result.get("trade_off_analysis", "")
            },
            confidence=ai_response.confidence
        )
        log_event(event)
        
        # Log goal conflicts if detected
        trade_offs = reasoning_result.get("trade_offs", [])
        if trade_offs:
            conflict_event = AgenticEvent.create(
                event_type=EventType.GOAL_CONFLICT_DETECTED,
                agent="AIEnhancedReasoningAgent",
                input_state={"trade_offs": trade_offs},
                decision={
                    "conflict_type": "product_trade_offs",
                    "severity": "medium"
                },
                output_state={"recommendations": reasoning_result.get("recommendations", [])},
                confidence=ai_response.confidence * 0.9
            )
            log_event(conflict_event)
    
    def generate_explanation(self, product: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """
        Generate a natural language explanation for why a product matches the intent.
        
        Args:
            product: Product to explain
            intent: User's structured intent
            
        Returns:
            Natural language explanation
        """
        try:
            prompt = f"""
Explain why this product is a good match for the user's shopping intent.

User Intent: {self._create_intent_summary(intent)}

Product Details:
{self._format_products_for_llm([product])}

Provide a clear, conversational explanation that a user would understand.
Focus on how the product meets their specific needs and preferences.
"""
            
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.5,
                max_tokens=500
            )
            
            return ai_response.content
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return f"Product {product.get('name', 'Unknown')} matches your criteria."
    
    def compare_products(self, product1: Dict[str, Any], product2: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two products and explain the differences.
        
        Args:
            product1: First product
            product2: Second product
            intent: User's structured intent
            
        Returns:
            Comparison analysis
        """
        try:
            prompt = f"""
Compare these two products for the user's shopping intent.

User Intent: {self._create_intent_summary(intent)}

Product 1:
{self._format_products_for_llm([product1])}

Product 2:
{self._format_products_for_llm([product2])}

Provide a detailed comparison focusing on:
1. Which product better matches the user's intent
2. Key differences and trade-offs
3. Which would be the better choice and why
4. Any potential drawbacks of each option
"""
            
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.6,
                max_tokens=800
            )
            
            return {
                "comparison": ai_response.content,
                "confidence": ai_response.confidence,
                "model": ai_response.model
            }
            
        except Exception as e:
            logger.error(f"Failed to compare products: {e}")
            return {
                "comparison": "Unable to generate comparison",
                "confidence": 0.0,
                "model": None
            }


# Global AI-enhanced reasoning agent instance
ai_reasoning_agent = AIEnhancedReasoningAgent()


def reason_products(intent_state: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function to reason about products using the AI-enhanced agent."""
    return ai_reasoning_agent.reason_products(intent_state, candidates)


def reason_products_ai(intent_state: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function to reason about products using the AI-enhanced agent."""
    return ai_reasoning_agent.reason_products(intent_state, candidates)


def generate_explanation_ai(product: Dict[str, Any], intent: Dict[str, Any]) -> str:
    """Convenience function to generate product explanation using the AI-enhanced agent."""
    return ai_reasoning_agent.generate_explanation(product, intent)


def compare_products_ai(product1: Dict[str, Any], product2: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to compare products using the AI-enhanced agent."""
    return ai_reasoning_agent.compare_products(product1, product2, intent)