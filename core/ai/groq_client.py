"""
Groq API Client for SHOP-BY-INTENTION System

Provides integration with Groq's Llama models for enhanced AI capabilities.
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import requests
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqModel(Enum):
    """Available Groq models."""
    LLAMA3_8B = "llama-3.1-8b-instant"
    LLAMA3_70B = "llama-3.3-70b-versatile"
    MIXTRAL_8X7B = "meta-llama/llama-4-scout-17b-16e-instruct"


@dataclass
class GroqResponse:
    """Structured response from Groq API."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float


class GroqClient:
    """Groq API client wrapper with enhanced features."""
    
    def __init__(self, api_key: Optional[str] = None, default_model: str = GroqModel.LLAMA3_8B.value):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            default_model: Default model to use
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY environment variable.")
        
        self.default_model = default_model
        self.client = Groq(api_key=self.api_key)
        self.rate_limit_delay = 5.0  # seconds between requests
        self.last_request_time = 0.0
        
        logger.info(f"Initialized Groq client with model: {self.default_model}")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        stream: bool = False
    ) -> GroqResponse:
        """
        Make a chat completion request to Groq API.
        
        Args:
            messages: List of messages in the conversation
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            stream: Whether to stream the response
            
        Returns:
            GroqResponse object with the completion
        """
        self._enforce_rate_limit()
        
        model = model or self.default_model
        
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if stream:
                # Handle streaming response
                content = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
            else:
                content = response.choices[0].message.content
            
            return GroqResponse(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def generate_embedding(self, text: str, model: str = "all-MiniLM-L6-v2") -> List[float]:
        """
        Generate embeddings for text using a local sentence-transformers model.
        Groq API does not support native embeddings, so we use a local fallback.
        
        Args:
            text: Text to generate embeddings for
            model: Model to use for embeddings (sentence-transformers)
            
        Returns:
            List of embedding values
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            # Lazy load the model to save memory if not used
            if not hasattr(self, '_embedding_model') or self._embedding_model is None:
                logger.info(f"Loading local embedding model: {model}")
                self._embedding_model = SentenceTransformer(model)
                
            embedding = self._embedding_model.encode(text)
            return embedding.tolist()
            
        except ImportError:
            logger.error("sentence-transformers not installed. Generating mock embedding.")
            # Generate a mock embedding of size 384 (standard for MiniLM)
            import numpy as np
            return np.random.rand(384).tolist()
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            import numpy as np
            return np.random.rand(384).tolist()
    
    def batch_chat_completion(
        self, 
        batch_requests: List[Dict[str, Any]], 
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple chat completion requests efficiently.
        
        Args:
            batch_requests: List of request dictionaries
            model: Model to use for all requests
            
        Returns:
            List of responses
        """
        responses = []
        
        for request in batch_requests:
            try:
                response = self.chat_completion(
                    messages=request["messages"],
                    model=model or self.default_model,
                    temperature=request.get("temperature", 0.7),
                    max_tokens=request.get("max_tokens"),
                    top_p=request.get("top_p", 1.0)
                )
                responses.append({
                    "success": True,
                    "response": response,
                    "request": request
                })
            except Exception as e:
                responses.append({
                    "success": False,
                    "error": str(e),
                    "request": request
                })
        
        return responses
    
    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific model."""
        model = model or self.default_model
        return {
            "model": model,
            "api_key_set": bool(self.api_key),
            "rate_limit_delay": self.rate_limit_delay
        }


# Global Groq client instance
groq_client = GroqClient()


def get_groq_client() -> GroqClient:
    """Get the global Groq client instance."""
    return groq_client


def set_groq_api_key(api_key: str):
    """Set the Groq API key globally."""
    global groq_client
    groq_client = GroqClient(api_key=api_key)


def set_default_model(model: str):
    """Set the default model globally."""
    global groq_client
    groq_client.default_model = model