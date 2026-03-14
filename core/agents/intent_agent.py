"""
AI-Enhanced Intent Agent for SHOP-BY-INTENTION System

Uses Groq Llama models for advanced natural language understanding and intent extraction.
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from core.ai.model_service import get_ai_service
from core.events.event_model import IntentState, AgenticEvent, EventType
from core.events.event_logger import log_event
from core.config.groq_config import get_config

# Configure logging
logger = logging.getLogger(__name__)


class AIEnhancedIntentAgent:
    """Enhanced Intent Agent using LLM for advanced NLP."""
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.config = get_config()
        self.intent_extraction_prompt = self._build_intent_extraction_prompt()
    
    def _build_intent_extraction_prompt(self) -> str:
        """Build the prompt template for intent extraction."""
        return """
You are an expert shopping assistant. Extract structured intent from user queries.

Extract the following fields:
- category: Product category (laptop, camera, monitor, etc.)
- purpose: Primary use case (gaming, coding, photography, etc.)
- budget: Maximum budget in USD (extract number, ignore currency symbols)
- preferences: List of specific features or requirements
- uncertainty: What information is unclear or missing

User Query: "{user_input}"

Return ONLY valid JSON format with no markdown blocks, no intro, no outro:
{{
  "category": "string or null",
  "purpose": "string or null", 
  "budget": number or null,
  "preferences": ["list", "of", "strings"],
  "uncertainty": "string or null"
}}

Be conservative - if you're unsure about a field, set it to null.
Only extract information explicitly mentioned in the query.
"""
    
    def parse_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse natural language input into structured intent using LLM.
        
        Args:
            user_input: User's natural language query
            
        Returns:
            Dictionary containing parsed intent with LLM confidence
        """
        logger.info(f"AI Intent Agent parsing: {user_input}")
        
        try:
            # Use LLM for intent extraction
            prompt = self.intent_extraction_prompt.format(user_input=user_input)
            
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.1,  # Lower temperature for more deterministic responses
                max_tokens=500
            )
            
            # Parse LLM response
            intent_data = self._parse_llm_response(ai_response.content)
            
            # Create intent state
            intent_state = IntentState(
                category=intent_data.get("category"),
                purpose=intent_data.get("purpose"),
                budget=intent_data.get("budget"),
                preferences=intent_data.get("preferences", []),
                uncertainty=intent_data.get("uncertainty")
            )
            
            # Log the intent parsing event
            event = AgenticEvent.create(
                event_type=EventType.INTENT_PARSED,
                agent="AIEnhancedIntentAgent",
                input_state={"user_input": user_input},
                decision={
                    "extraction_method": "llm",
                    "llm_model": ai_response.model,
                    "llm_confidence": ai_response.confidence,
                    "llm_response_time": ai_response.metadata.get("response_time", 0)
                },
                output_state=intent_state.to_dict(),
                confidence=ai_response.confidence
            )
            log_event(event)
            
            # Check for uncertainty
            if intent_state.uncertainty:
                uncertainty_event = AgenticEvent.create(
                    event_type=EventType.INTENT_UNCERTAIN,
                    agent="AIEnhancedIntentAgent",
                    input_state=intent_state.to_dict(),
                    decision={
                        "uncertainty_detected": True,
                        "uncertainty_description": intent_state.uncertainty
                    },
                    output_state=intent_state.to_dict(),
                    confidence=ai_response.confidence * 0.8  # Lower confidence for uncertain intent
                )
                log_event(uncertainty_event)
            
            logger.info(f"AI Intent parsed: {intent_state.to_dict()}")
            return intent_state.to_dict()
            
        except Exception as e:
            logger.error(f"AI Intent parsing failed: {e}")
            # Fallback to rule-based parsing
            return self._fallback_intent_parsing(user_input)
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured intent data."""
        try:
            # Strip markdown code blocks if the LLM provided them anyway
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', cleaned)
            if json_match:
                json_str = json_match.group()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as json_err:
                    logger.warning(f"Failed to decode JSON: {json_err}, falling back to pattern matching")
            
            # If JSON parsing fails, try to extract key-value pairs
            intent_data = {
                "category": None,
                "purpose": None,
                "budget": None,
                "preferences": [],
                "uncertainty": None
            }
            
            # Simple pattern matching for fallback
            lines = cleaned.split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().strip('"\'')
                    value = value.strip().strip('"\'')
                    
                    if key == 'category':
                        intent_data["category"] = value if value.lower() != 'null' else None
                    elif key == 'purpose':
                        intent_data["purpose"] = value if value.lower() != 'null' else None
                    elif key == 'budget':
                        try:
                            digits = re.findall(r'\d+', value)
                            intent_data["budget"] = float(digits[0]) if digits else None
                        except:
                            intent_data["budget"] = None
                    elif key == 'preferences':
                        # Extract list from string
                        prefs = value.strip('[]').split(',')
                        intent_data["preferences"] = [p.strip().strip('"\'') for p in prefs if p.strip()]
                    elif key == 'uncertainty':
                        intent_data["uncertainty"] = value if value.lower() != 'null' else None
            
            return intent_data
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "category": None,
                "purpose": None,
                "budget": None,
                "preferences": [],
                "uncertainty": "Failed to parse response"
            }
    
    def _fallback_intent_parsing(self, user_input: str) -> Dict[str, Any]:
        """Fallback to rule-based intent parsing if LLM fails."""
        logger.warning("Falling back to rule-based intent parsing")
        
        # Import the original intent agent for fallback
        from .intent_agent import IntentAgent
        
        fallback_agent = IntentAgent()
        return fallback_agent.parse_intent(user_input)
    
    def extract_entities(self, user_input: str) -> Dict[str, List[str]]:
        """
        Extract entities from user input using LLM.
        
        Args:
            user_input: User's natural language query
            
        Returns:
            Dictionary of extracted entities
        """
        try:
            prompt = f"""
Extract entities from this shopping query:

Query: "{user_input}"

Extract these entity types:
- brands: Company names (Apple, Dell, etc.)
- features: Product features (lightweight, RGB, etc.)
- specifications: Technical specs (16GB RAM, RTX 4060, etc.)
- constraints: Limitations or requirements (under $1000, portable, etc.)

Return JSON format:
{{
  "brands": ["list", "of", "brands"],
  "features": ["list", "of", "features"],
  "specifications": ["list", "of", "specs"],
  "constraints": ["list", "of", "constraints"]
}}
"""
            
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.3,
                max_tokens=300
            )
            
            # Parse entities
            try:
                entities = json.loads(ai_response.content)
                return entities
            except:
                return {
                    "brands": [],
                    "features": [],
                    "specifications": [],
                    "constraints": []
                }
                
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {
                "brands": [],
                "features": [],
                "specifications": [],
                "constraints": []
            }
    
    def understand_context(self, conversation_history: List[Dict[str, str]], current_query: str) -> Dict[str, Any]:
        """
        Understand context from conversation history using LLM.
        
        Args:
            conversation_history: List of previous messages
            current_query: Current user query
            
        Returns:
            Context understanding with inferred preferences and constraints
        """
        try:
            # Build conversation context
            context = ""
            for msg in conversation_history[-3:]:  # Last 3 messages
                context += f"{msg['role']}: {msg['content']}\n"
            context += f"User: {current_query}"
            
            prompt = f"""
Analyze this conversation context for shopping intent:

Context:
{context}

Identify:
1. User's shopping intent and preferences
2. Any constraints or requirements mentioned
3. What the user is looking for
4. Any unresolved questions or missing information

Return JSON format:
{{
  "intent_summary": "summary of user intent",
  "identified_preferences": ["list", "of", "preferences"],
  "constraints": ["list", "of", "constraints"],
  "missing_information": ["list", "of", "missing info"],
  "context_confidence": 0.0 to 1.0
}}
"""
            
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.5,
                max_tokens=500
            )
            
            try:
                context_data = json.loads(ai_response.content)
                return context_data
            except:
                return {
                    "intent_summary": "Unable to parse context",
                    "identified_preferences": [],
                    "constraints": [],
                    "missing_information": [],
                    "context_confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"Context understanding failed: {e}")
            return {
                "intent_summary": "Error in context analysis",
                "identified_preferences": [],
                "constraints": [],
                "missing_information": [],
                "context_confidence": 0.0
            }


# Global AI-enhanced intent agent instance
ai_intent_agent = AIEnhancedIntentAgent()


def parse_intent(user_input: str) -> Dict[str, Any]:
    """Parse intent using the AI-enhanced agent."""
    return ai_intent_agent.parse_intent(user_input)


def parse_intent_ai(user_input: str) -> Dict[str, Any]:
    """Convenience function to parse intent using the AI-enhanced agent."""
    return ai_intent_agent.parse_intent(user_input)


def extract_entities_ai(user_input: str) -> Dict[str, List[str]]:
    """Convenience function to extract entities using the AI-enhanced agent."""
    return ai_intent_agent.extract_entities(user_input)


def understand_context_ai(conversation_history: List[Dict[str, str]], current_query: str) -> Dict[str, Any]:
    """Convenience function to understand context using the AI-enhanced agent."""
    return ai_intent_agent.understand_context(conversation_history, current_query)