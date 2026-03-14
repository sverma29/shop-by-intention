"""
AI Model Service for SHOP-BY-INTENTION System

Provides a unified interface for AI model operations with fallback capabilities.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer

from core.ai.groq_client import GroqClient, GroqResponse, GroqModel
from core.events.event_model import AgenticEvent, EventType
from core.events.event_logger import log_event

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Structured response from AI models."""
    content: str
    model: str
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class EmbeddingResponse:
    """Structured embedding response."""
    embeddings: List[List[float]]
    model: str
    dimension: int


class AIModelInterface(ABC):
    """Abstract interface for AI model operations."""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> AIResponse:
        """Generate text using the model."""
        pass
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> EmbeddingResponse:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        pass


class GroqModelService(AIModelInterface):
    """Groq model service implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = GroqModel.LLAMA3_8B.value):
        self.groq_client = GroqClient(api_key, model)
    
    def generate_text(self, prompt: str, **kwargs) -> AIResponse:
        """Generate text using Groq API."""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = self.groq_client.chat_completion(
                messages=messages,
                model=kwargs.get("model"),
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 500),
                top_p=kwargs.get("top_p", 1.0)
            )
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(response)
            
            # Log the AI response
            self._log_ai_response("text_generation", prompt, response, confidence)
            
            return AIResponse(
                content=response.content,
                model=response.model,
                confidence=confidence,
                metadata={
                    "usage": response.usage,
                    "response_time": response.response_time,
                    "finish_reason": response.finish_reason
                }
            )
            
        except Exception as e:
            logger.error(f"Groq text generation failed: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> EmbeddingResponse:
        """Generate embeddings using Groq (placeholder implementation)."""
        try:
            # For now, use a simple fallback since Groq doesn't have dedicated embedding API
            embeddings = []
            for text in texts:
                embedding = self.groq_client.generate_embedding(text)
                embeddings.append(embedding)
            
            dimension = len(embeddings[0]) if embeddings else 0
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=self.groq_client.default_model,
                dimension=dimension
            )
            
        except Exception as e:
            logger.error(f"Groq embedding generation failed: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Groq model information."""
        return self.groq_client.get_model_info()
    
    def _calculate_confidence(self, response: GroqResponse) -> float:
        """Calculate confidence score for the response."""
        # Simple confidence calculation based on response characteristics
        confidence = 0.8  # Base confidence
        
        # Adjust based on finish reason
        if response.finish_reason == "stop":
            confidence += 0.1
        elif response.finish_reason == "length":
            confidence -= 0.1
        
        # Adjust based on response time (faster responses might be more confident)
        if response.response_time < 2.0:
            confidence += 0.05
        
        return max(0.1, min(1.0, confidence))
    
    def _log_ai_response(self, operation: str, prompt: str, response: GroqResponse, confidence: float):
        """Log AI response for monitoring and debugging."""
        event = AgenticEvent.create(
            event_type=EventType.REASONING_PATH_CHOSEN,  # Using this for AI operations
            agent="GroqModelService",
            input_state={
                "operation": operation,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
            },
            decision={
                "model": response.model,
                "confidence": confidence,
                "response_time": response.response_time,
                "tokens_used": response.usage["total_tokens"]
            },
            output_state={
                "response_length": len(response.content),
                "finish_reason": response.finish_reason
            },
            confidence=confidence
        )
        log_event(event)


class LocalModelService(AIModelInterface):
    """Local model service using Sentence Transformers for embeddings."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model)
        logger.info(f"Initialized local model service with {embedding_model}")
    
    def generate_text(self, prompt: str, **kwargs) -> AIResponse:
        """Generate text using a small local model fallback via huggingface transformers."""
        try:
            from transformers import pipeline
            import time
            
            # Use a small fast model for fallback. In production, this might be a larger local model.
            generator = pipeline('text-generation', model='gpt2', device=-1)
            
            start_time = time.time()
            max_new_tokens = kwargs.get("max_tokens", 50)
            
            # Generate text
            output = generator(prompt, max_new_tokens=max_new_tokens, num_return_sequences=1)
            generated_text = output[0]['generated_text']
            
            # Remove the prompt from the output
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
                
            response_time = time.time() - start_time
            
            return AIResponse(
                content=generated_text,
                model="local-gpt2",
                confidence=0.5, # Lower confidence for fallback
                metadata={
                    "usage": {"total_tokens": max_new_tokens},
                    "response_time": response_time,
                    "finish_reason": "length"
                }
            )
        except ImportError:
            logger.error("transformers library is not installed for local model fallback.")
            raise NotImplementedError("Local text generation requires transformers library.")
        except Exception as e:
            logger.error(f"Local text generation failed: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> EmbeddingResponse:
        """Generate embeddings using local Sentence Transformer."""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
            
            # Convert to list format
            embeddings_list = embeddings.tolist()
            
            return EmbeddingResponse(
                embeddings=embeddings_list,
                model=self.embedding_model._model_card_data.model_name,
                dimension=len(embeddings_list[0]) if embeddings_list else 0
            )
            
        except Exception as e:
            logger.error(f"Local embedding generation failed: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get local model information."""
        return {
            "model": "Local Sentence Transformer",
            "type": "Embedding",
            "dimensions": 384  # Default for all-MiniLM-L6-v2
        }


class AIModelService:
    """Unified AI model service with fallback capabilities."""
    
    def __init__(self, 
                 groq_api_key: Optional[str] = None,
                 primary_model: str = GroqModel.LLAMA3_8B.value,
                 fallback_to_local: bool = True):
        """
        Initialize AI model service.
        
        Args:
            groq_api_key: Groq API key
            primary_model: Primary Groq model to use
            fallback_to_local: Whether to fallback to local models on failure
        """
        self.groq_service = GroqModelService(groq_api_key, primary_model)
        self.local_service = LocalModelService() if fallback_to_local else None
        self.fallback_to_local = fallback_to_local
    
    def generate_text(self, prompt: str, **kwargs) -> AIResponse:
        """Generate text with fallback to local models."""
        try:
            return self.groq_service.generate_text(prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Groq text generation failed, falling back: {e}")
            
            if self.fallback_to_local:
                # For text generation, we don't have a good local fallback yet
                # Return a simple response or raise the original error
                raise e
            else:
                raise e
    
    def generate_embeddings(self, texts: List[str]) -> EmbeddingResponse:
        """Generate embeddings with fallback to local models."""
        try:
            return self.groq_service.generate_embeddings(texts)
        except Exception as e:
            logger.warning(f"Groq embedding generation failed, falling back to local: {e}")
            
            if self.fallback_to_local:
                return self.local_service.generate_embeddings(texts)
            else:
                raise e
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the primary model."""
        return self.groq_service.get_model_info()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        try:
            # Generate embeddings for both texts
            embeddings_response = self.generate_embeddings([text1, text2])
            embeddings = embeddings_response.embeddings
            
            if len(embeddings) != 2:
                raise ValueError("Failed to generate embeddings for similarity calculation")
            
            # Calculate cosine similarity
            similarity = 1 - cosine(embeddings[0], embeddings[1])
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def find_similar_texts(self, query_text: str, candidate_texts: List[str], top_k: int = 5) -> List[Tuple[int, float]]:
        """Find the most similar texts to the query."""
        try:
            # Generate embeddings for all texts
            all_texts = [query_text] + candidate_texts
            embeddings_response = self.generate_embeddings(all_texts)
            embeddings = embeddings_response.embeddings
            
            query_embedding = embeddings[0]
            candidate_embeddings = embeddings[1:]
            
            # Calculate similarities
            similarities = []
            for i, candidate_embedding in enumerate(candidate_embeddings):
                similarity = 1 - cosine(query_embedding, candidate_embedding)
                similarities.append((i, float(similarity)))
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Similar text search failed: {e}")
            return []


# Global AI model service instance
ai_service = AIModelService()


def get_ai_service() -> AIModelService:
    """Get the global AI model service instance."""
    return ai_service


def set_groq_api_key(api_key: str):
    """Set the Groq API key for the global service."""
    global ai_service
    ai_service = AIModelService(groq_api_key=api_key)


def set_primary_model(model: str):
    """Set the primary model for the global service."""
    global ai_service
    ai_service = AIModelService(primary_model=model)