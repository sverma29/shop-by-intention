"""
AI-Enhanced Retrieval Agent for SHOP-BY-INTENTION System

Uses semantic search and LLM for intelligent product retrieval and ranking.
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


class AIEnhancedRetrievalAgent:
    """Enhanced Retrieval Agent using semantic search and LLM ranking."""
    
    def __init__(self, catalog_path: str = "data/product_catalog.json"):
        """
        Initialize the AI-enhanced retrieval agent.
        
        Args:
            catalog_path: Path to the product catalog file
        """
        self.catalog_path = catalog_path
        self.products = self._load_catalog()
        self.ai_service = get_ai_service()
        self.config = get_config()
        
        # Precompute product embeddings for semantic search
        self.product_embeddings = {}
        self._precompute_embeddings()
    
    def _load_catalog(self) -> List[Dict[str, Any]]:
        """Load product catalog from JSON file."""
        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Product catalog not found at {self.catalog_path}")
            return []
    
    def _precompute_embeddings(self):
        """Precompute embeddings for all products."""
        if not self.products:
            return
        
        logger.info("Precomputing product embeddings...")
        
        # Create product descriptions for embedding
        product_descriptions = []
        for product in self.products:
            description = self._create_product_description(product)
            product_descriptions.append(description)
        
        # Generate embeddings
        try:
            embedding_response = self.ai_service.generate_embeddings(product_descriptions)
            
            for i, product in enumerate(self.products):
                if i < len(embedding_response.embeddings):
                    self.product_embeddings[product["id"]] = embedding_response.embeddings[i]
            
            logger.info(f"Computed embeddings for {len(self.product_embeddings)} products")
            
        except Exception as e:
            logger.error(f"Failed to compute embeddings: {e}")
    
    def _create_product_description(self, product: Dict[str, Any]) -> str:
        """Create a text description for a product."""
        features = ", ".join(product.get("features", []))
        purpose_list = ", ".join(product.get("purpose", []))
        
        description = f"""
        {product.get('name', '')} by {product.get('brand', '')}
        Category: {product.get('category', '')}
        Purpose: {purpose_list}
        Price: ${product.get('price', 0)}
        Features: {features}
        """
        
        return description.strip()
    
    def retrieve_products(self, intent_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve products using semantic search and LLM ranking.
        
        Args:
            intent_state: Structured intent state
            
        Returns:
            List of relevant products with AI-enhanced scoring
        """
        logger.info(f"AI Retrieval Agent processing intent: {intent_state}")
        
        # Create query text from intent
        query_text = self._create_query_text(intent_state)
        
        # Perform semantic search
        semantic_candidates = self._semantic_search(query_text, top_k=20)
        
        # Apply budget filtering if specified
        budget = intent_state.get("budget")
        if budget:
            semantic_candidates = self._filter_by_budget(semantic_candidates, budget)
        
        # Use LLM for intelligent ranking and filtering
        ranked_candidates = self._llm_rank_candidates(query_text, semantic_candidates, intent_state)
        
        # Log retrieval results
        self._log_retrieval_event(intent_state, query_text, ranked_candidates)
        
        logger.info(f"Retrieved {len(ranked_candidates)} products using AI")
        return ranked_candidates
    
    def _create_query_text(self, intent: Dict[str, Any]) -> str:
        """Create a search query text from intent."""
        parts = []
        
        if intent.get("category"):
            parts.append(f"category: {intent['category']}")
        if intent.get("purpose"):
            parts.append(f"purpose: {intent['purpose']}")
        if intent.get("preferences"):
            parts.append(f"preferences: {', '.join(intent['preferences'])}")
        if intent.get("budget"):
            parts.append(f"budget: under ${intent['budget']}")
        
        return " ".join(parts)
    
    def _semantic_search(self, query_text: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings."""
        if not self.product_embeddings:
            logger.warning("No precomputed embeddings available, using fallback search")
            return self._fallback_search(query_text, top_k)
        
        try:
            # Generate query embedding
            query_embedding_response = self.ai_service.generate_embeddings([query_text])
            query_embedding = query_embedding_response.embeddings[0]
            
            # Calculate similarities
            similarities = []
            for product in self.products:
                product_id = product["id"]
                if product_id in self.product_embeddings:
                    product_embedding = self.product_embeddings[product_id]
                    similarity = self.ai_service.calculate_similarity(
                        query_text, self._create_product_description(product)
                    )
                    similarities.append((product, similarity))
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [product for product, _ in similarities[:top_k]]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return self._fallback_search(query_text, top_k)
    
    def _llm_rank_candidates(self, query_text: str, candidates: List[Dict[str, Any]], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM to rank and filter candidates."""
        if not candidates:
            return []
        
        try:
            # Create product summaries for LLM
            product_summaries = []
            for product in candidates:
                summary = f"""
                ID: {product['id']}
                Name: {product['name']}
                Brand: {product['brand']}
                Category: {product['category']}
                Price: ${product['price']}
                Purpose: {', '.join(product.get('purpose', []))}
                Features: {', '.join(product.get('features', []))}
                """
                product_summaries.append(summary)
            
            # Create LLM prompt for ranking
            prompt = f"""
            You are an expert shopping assistant. Rank these products based on how well they match the user's intent.

            User Intent: {query_text}

            Products to rank:
            {chr(10).join(product_summaries)}

            Instructions:
            1. Rank products from best match to worst match
            2. Consider category, purpose, budget, and preferences
            3. Remove products that clearly don't match
            4. Return the top 10 most relevant products

            Return JSON format:
            {{
              "ranked_products": [
                {{"id": "product_id", "reason": "why this product matches"}},
                ...
              ]
            }}
            """
            
            ai_response = self.ai_service.generate_text(
                prompt=prompt,
                model=self.config.default_model,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse LLM response
            ranked_products = self._parse_llm_ranking_response(ai_response.content, candidates)
            
            return ranked_products
            
        except Exception as e:
            logger.error(f"LLM ranking failed: {e}")
            return candidates[:10]  # Return first 10 as fallback
    
    def _parse_llm_ranking_response(self, response_text: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse LLM ranking response."""
        try:
            # Strip markdown formatting
            cleaned_response = response_text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            # Try to extract JSON using regex if stripping didn't work perfectly
            import re
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            
            if json_match:
                json_data = json.loads(json_match.group())
                
                ranked_ids = [item["id"] for item in json_data.get("ranked_products", [])]
                
                # Reorder candidates based on LLM ranking
                ranked_candidates = []
                for product_id in ranked_ids:
                    for product in candidates:
                        if product["id"] == product_id:
                            ranked_candidates.append(product)
                            break
                
                return ranked_candidates
            
            # Fallback: return original candidates
            return candidates[:10]
            
        except Exception as e:
            logger.error(f"Failed to parse LLM ranking response: {e}")
            return candidates[:10]
    
    def _filter_by_budget(self, products: List[Dict[str, Any]], budget: float) -> List[Dict[str, Any]]:
        """Filter products by budget."""
        return [p for p in products if p.get("price", 0) <= budget]
    
    def _fallback_search(self, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback search using text matching."""
        # Simple keyword-based search as fallback
        query_words = query_text.lower().split()
        scored_products = []
        
        for product in self.products:
            product_text = self._create_product_description(product).lower()
            score = sum(1 for word in query_words if word in product_text)
            scored_products.append((product, score))
        
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return [product for product, score in scored_products[:top_k]]
    
    def _log_retrieval_event(self, intent_state: Dict[str, Any], query_text: str, candidates: List[Dict[str, Any]]):
        """Log the retrieval event."""
        event = AgenticEvent.create(
            event_type=EventType.RETRIEVAL_STRATEGY_SELECTED,
            agent="AIEnhancedRetrievalAgent",
            input_state={
                "intent": intent_state,
                "query_text": query_text
            },
            decision={
                "retrieval_method": "semantic_search_with_llm_ranking",
                "candidates_found": len(candidates),
                "ai_model_used": self.config.default_model
            },
            output_state={
                "top_candidates": [p["id"] for p in candidates[:5]],
                "candidates_count": len(candidates)
            },
            confidence=0.9
        )
        log_event(event)
        
        # Log context acceptance/rejection
        context_event = AgenticEvent.create(
            event_type=EventType.CONTEXT_ACCEPTED if candidates else EventType.CONTEXT_REJECTED,
            agent="AIEnhancedRetrievalAgent",
            input_state={"candidates_count": len(candidates)},
            decision={
                "semantic_search_used": True,
                "llm_ranking_used": True
            },
            output_state={"retrieved_products": len(candidates)},
            confidence=0.8 if candidates else 0.2
        )
        log_event(context_event)


# Global AI-enhanced retrieval agent instance
ai_retrieval_agent = AIEnhancedRetrievalAgent()


def retrieve_products(intent_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience function to retrieve products using the AI-enhanced agent."""
    return ai_retrieval_agent.retrieve_products(intent_state)


def retrieve_products_ai(intent_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience function to retrieve products using the AI-enhanced agent."""
    return ai_retrieval_agent.retrieve_products(intent_state)
