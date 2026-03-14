"""
AI-Enhanced Clarification Agent for SHOP-BY-INTENTION System

Uses LLM for natural, context-aware clarification questions and multi-turn dialogue.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from core.ai.model_service import get_ai_service
from core.events.event_model import IntentState, AgenticEvent, EventType
from core.events.event_logger import log_event
from core.config.groq_config import get_config

# Configure logging
logger = logging.getLogger(__name__)


class AIEnhancedClarificationAgent:
    """Enhanced Clarification Agent using LLM for conversational clarification."""
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.config = get_config()
        self.clarification_prompt = self._build_clarification_prompt()
    
    def _build_clarification_prompt(self) -> str:
        """Build the prompt template for clarification."""
        return """
You are a helpful shopping assistant. The user has provided a shopping request, but some information is unclear or missing.

User's Original Request: "{user_input}"

Current Understanding:
{current_intent}

Missing/Unclear Information:
{uncertainty_description}

Your Task:
1. Ask ONE clear, specific question to clarify the missing information
2. Make the question conversational and natural
3. Provide helpful examples or options when appropriate
4. Keep the question focused on a single piece of information
5. Use a friendly, helpful tone

Examples of good clarification questions:
- "What's your budget range for this purchase? For example, are you looking to spend under $500, $500-$1000, or more than $1000?"
- "What will you primarily use this [product category] for? For example, gaming, work, or casual browsing?"
- "Are there any specific features you're looking for? For example, do you need something lightweight, with long battery life, or with specific connectivity options?"

Return your response as a single clarification question.
"""
    
    def clarify_intent(self, intent_state: Dict[str, Any], user_input: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Clarify ambiguous intent using LLM for natural conversation.
        
        Args:
            intent_state: Current intent state
            user_input: Original user input
            conversation_history: Previous conversation messages
            
        Returns:
            Updated intent state with clarification and AI-generated question
        """
        logger.info(f"AI Clarification Agent processing uncertainty: {intent_state.get('uncertainty')}")
        
        intent = IntentState.from_dict(intent_state)
        
        # Check for uncertainties
        uncertainties = self._identify_uncertainties(intent)
        
        if not uncertainties:
            # No clarification needed
            refined_event = AgenticEvent.create(
                event_type=EventType.INTENT_REFINED,
                agent="AIEnhancedClarificationAgent",
                input_state=intent_state,
                decision={"clarification_needed": False},
                output_state=intent_state,
                confidence=1.0
            )
            log_event(refined_event)
            return intent_state
        
        # Generate AI clarification question
        clarification_question = self._generate_clarification_question(
            user_input, intent_state, uncertainties, conversation_history
        )
        
        # Log clarification request
        clarification_event = AgenticEvent.create(
            event_type=EventType.CLARIFICATION_REQUESTED,
            agent="AIEnhancedClarificationAgent",
            input_state=intent_state,
            decision={
                "uncertainties": uncertainties,
                "ai_question": clarification_question,
                "conversation_context": bool(conversation_history)
            },
            output_state=intent_state,
            confidence=0.9
        )
        log_event(clarification_event)
        
        # For simulation purposes, we'll provide smart mock responses
        # In a real system, this would wait for user response
        mock_response = self._generate_smart_mock_response(uncertainties, user_input, intent_state)
        
        # Update intent with mock response
        updated_intent = self._update_intent_with_response(intent, uncertainties[0], mock_response)
        
        # Log intent refinement
        refined_event = AgenticEvent.create(
            event_type=EventType.INTENT_REFINED,
            agent="AIEnhancedClarificationAgent",
            input_state=intent_state,
            decision={
                "uncertainties_resolved": uncertainties,
                "mock_response_used": True,
                "ai_question": clarification_question,
                "generated_response": mock_response
            },
            output_state=updated_intent.to_dict(),
            confidence=0.8
        )
        log_event(refined_event)
        
        return {
            **updated_intent.to_dict(),
            "clarification_question": clarification_question,
            "mock_response": mock_response
        }
    
    def _identify_uncertainties(self, intent: IntentState) -> List[str]:
        """Identify what aspects of the intent are uncertain."""
        uncertainties = []
        
        if not intent.category:
            uncertainties.append("category")
        if not intent.budget:
            uncertainties.append("budget")
        if not intent.purpose:
            uncertainties.append("purpose")
        
        return uncertainties
    
    def _generate_clarification_question(self, user_input: str, intent_state: Dict[str, Any], uncertainties: List[str], conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Generate a natural clarification question using LLM."""
        try:
            # Create context from conversation history
            context = ""
            if conversation_history:
                context = "Previous conversation:\n"
                for msg in conversation_history[-2:]:  # Last 2 messages
                    context += f"{msg['role']}: {msg['content']}\n"
            
            # Create uncertainty description
            uncertainty_desc = ", ".join(uncertainties)
            
            # Build prompt
            prompt = self.clarification_prompt.format(
                user_input=user_input,
                current_intent=self._format_intent_for_prompt(intent_state),
                uncertainty_description=uncertainty_desc
            )
            
            if context:
                prompt += f"\n\n{context}"
            
            # Get LLM response
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.7,  # Higher temperature for more natural, varied responses
                max_tokens=200
            )
            
            return ai_response.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate clarification question: {e}")
            # Fallback to simple question
            return f"What information can you provide about: {', '.join(uncertainties)}?"
    
    def _format_intent_for_prompt(self, intent: Dict[str, Any]) -> str:
        """Format intent for LLM prompt."""
        parts = []
        
        if intent.get("category"):
            parts.append(f"Category: {intent['category']}")
        if intent.get("purpose"):
            parts.append(f"Purpose: {intent['purpose']}")
        if intent.get("budget"):
            parts.append(f"Budget: ${intent['budget']}")
        if intent.get("preferences"):
            parts.append(f"Preferences: {', '.join(intent['preferences'])}")
        
        return " | ".join(parts) if parts else "No clear intent identified"
    
    def _generate_smart_mock_response(self, uncertainties: List[str], user_input: str, intent_state: Dict[str, Any]) -> str:
        """Generate intelligent mock responses based on context."""
        if "category" in uncertainties:
            # Try to infer category from user input
            user_lower = user_input.lower()
            if any(word in user_lower for word in ["laptop", "notebook", "computer"]):
                return "laptop"
            elif any(word in user_lower for word in ["camera", "photo", "picture"]):
                return "camera"
            elif any(word in user_lower for word in ["monitor", "screen", "display"]):
                return "monitor"
            else:
                return "laptop"  # Default assumption
        
        elif "budget" in uncertainties:
            # Try to infer budget from context or provide reasonable default
            user_lower = user_input.lower()
            if "cheap" in user_lower or "budget" in user_lower:
                return "500"
            elif "expensive" in user_lower or "premium" in user_lower:
                return "2000"
            elif "under" in user_lower:
                # Try to extract number after "under"
                import re
                match = re.search(r'under\s*\$?(\d+)', user_lower)
                if match:
                    return match.group(1)
            return "1000"  # Default budget
        
        elif "purpose" in uncertainties:
            # Try to infer purpose from context
            user_lower = user_input.lower()
            if any(word in user_lower for word in ["gaming", "game", "play"]):
                return "gaming"
            elif any(word in user_lower for word in ["coding", "programming", "develop"]):
                return "coding"
            elif any(word in user_lower for word in ["travel", "portable", "lightweight"]):
                return "travel"
            elif any(word in user_lower for word in ["photography", "photo", "picture"]):
                return "photography"
            else:
                return "general use"
        
        return "Not specified"
    
    def _update_intent_with_response(self, intent: IntentState, uncertainty: str, response: str) -> IntentState:
        """Update intent state with clarification response."""
        if uncertainty == "category":
            intent.category = response
        elif uncertainty == "budget":
            try:
                intent.budget = float(response)
            except ValueError:
                intent.budget = None
        elif uncertainty == "purpose":
            intent.purpose = response
        
        # Clear uncertainty since we've resolved it
        intent.uncertainty = None
        
        return intent
    
    def handle_multi_turn_dialogue(self, user_input: str, current_intent: Dict[str, Any], conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Handle multi-turn clarification dialogue.
        
        Args:
            user_input: User's response to clarification
            current_intent: Current intent state
            conversation_history: Full conversation history
            
        Returns:
            Updated intent state after processing user response
        """
        try:
            # Use LLM to understand user's clarification response
            prompt = f"""
            Context: Shopping assistant clarifying user requirements
            
            Conversation History:
            {self._format_conversation_history(conversation_history)}
            
            User's Latest Response: "{user_input}"
            
            Current Intent Understanding:
            {self._format_intent_for_prompt(current_intent)}
            
            Task: Analyze the user's response and extract any new information that clarifies their intent.
            Update the intent state accordingly.
            
            Return JSON format:
            {{
              "updated_intent": {{
                "category": "string or null",
                "purpose": "string or null",
                "budget": number or null,
                "preferences": ["list", "of", "strings"],
                "uncertainty": "string or null"
              }},
              "new_information_extracted": true/false,
              "confidence": 0.0 to 1.0
            }}
            """
            
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.5,
                max_tokens=500
            )
            
            # Parse response
            try:
                response_data = json.loads(ai_response.content)
                updated_intent = response_data.get("updated_intent", current_intent)
                
                # Log the multi-turn dialogue event
                self._log_multi_turn_event(user_input, current_intent, updated_intent, ai_response)
                
                return updated_intent
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse multi-turn dialogue response")
                return current_intent
                
        except Exception as e:
            logger.error(f"Multi-turn dialogue handling failed: {e}")
            return current_intent
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for LLM."""
        formatted = []
        for msg in history:
            formatted.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(formatted)
    
    def _log_multi_turn_event(self, user_input: str, old_intent: Dict[str, Any], new_intent: Dict[str, Any], ai_response):
        """Log multi-turn dialogue event."""
        event = AgenticEvent.create(
            event_type=EventType.INTENT_REFINED,
            agent="AIEnhancedClarificationAgent",
            input_state={
                "user_input": user_input,
                "old_intent": old_intent
            },
            decision={
                "dialogue_type": "multi_turn",
                "new_information_extracted": True,
                "llm_model": ai_response.model,
                "response_time": ai_response.metadata.get("response_time", 0)
            },
            output_state=new_intent,
            confidence=ai_response.confidence
        )
        log_event(event)


# Global AI-enhanced clarification agent instance
ai_clarification_agent = AIEnhancedClarificationAgent()


def clarify_intent(intent_state: Dict[str, Any], user_input: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """Convenience function to clarify intent using the AI-enhanced agent."""
    return ai_clarification_agent.clarify_intent(intent_state, user_input, conversation_history)


def clarify_intent_ai(intent_state: Dict[str, Any], user_input: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """Convenience function to clarify intent using the AI-enhanced agent."""
    return ai_clarification_agent.clarify_intent(intent_state, user_input, conversation_history)


def handle_multi_turn_dialogue_ai(user_input: str, current_intent: Dict[str, Any], conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Convenience function to handle multi-turn dialogue using the AI-enhanced agent."""
    return ai_clarification_agent.handle_multi_turn_dialogue(user_input, current_intent, conversation_history)