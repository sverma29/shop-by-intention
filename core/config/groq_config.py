"""
Configuration management for Groq AI integration.

Handles API keys, model settings, and other configuration parameters.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json


class Environment(Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class GroqConfig:
    """Configuration for Groq AI integration."""
    
    # API Configuration
    api_key: Optional[str] = None
    base_url: str = "https://api.groq.com/openai/v1"
    timeout: int = 30
    max_retries: int = 5
    rate_limit_delay: float = 5.0
    
    # Model Configuration
    default_model: str = "llama3-8b-8192"
    available_models: list = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    
    # Cost and Usage
    cost_per_1k_tokens: Dict[str, float] = None
    daily_budget_limit: Optional[float] = None
    monthly_budget_limit: Optional[float] = None
    
    # Fallback Configuration
    enable_fallback: bool = True
    fallback_model: str = "llama3-8b-8192"
    local_embedding_model: str = "all-MiniLM-L6-v2"
    
    # Logging and Monitoring
    log_level: str = "INFO"
    enable_usage_logging: bool = True
    enable_performance_monitoring: bool = True
    
    # Feature Flags
    enable_semantic_search: bool = True
    enable_llm_reasoning: bool = True
    enable_conversational_clarification: bool = True
    enable_intent_extraction: bool = True
    
    def __post_init__(self):
        """Initialize default values."""
        if self.available_models is None:
            self.available_models = [
                "llama3-8b-8192",
                "llama3-70b-8192", 
                "llama2-70b-4096",
                "mixtral-8x7b-32768",
                "gemma-7b-it"
            ]
        
        if self.cost_per_1k_tokens is None:
            self.cost_per_1k_tokens = {
                "llama3-8b-8192": 0.00005,      # $0.05 per 1K tokens
                "llama3-70b-8192": 0.00019,     # $0.19 per 1K tokens
                "llama2-70b-4096": 0.00019,     # $0.19 per 1K tokens
                "mixtral-8x7b-32768": 0.00024,  # $0.24 per 1K tokens
                "gemma-7b-it": 0.00007          # $0.07 per 1K tokens
            }


class ConfigManager:
    """Manages application configuration with environment variable support."""
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config = self._load_config()
    
    def _load_config(self) -> GroqConfig:
        """Load configuration from environment variables and defaults."""
        # Load API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        
        # Load model settings
        default_model = os.getenv("GROQ_DEFAULT_MODEL", "llama3-8b-8192")
        max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "1000"))
        temperature = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
        top_p = float(os.getenv("GROQ_TOP_P", "1.0"))
        
        # Load cost settings
        daily_budget = os.getenv("GROQ_DAILY_BUDGET")
        monthly_budget = os.getenv("GROQ_MONTHLY_BUDGET")
        
        # Load feature flags
        enable_semantic_search = os.getenv("ENABLE_SEMANTIC_SEARCH", "true").lower() == "true"
        enable_llm_reasoning = os.getenv("ENABLE_LLM_REASONING", "true").lower() == "true"
        enable_conversational_clarification = os.getenv("ENABLE_CONVERSATIONAL_CLARIFICATION", "true").lower() == "true"
        enable_intent_extraction = os.getenv("ENABLE_INTENT_EXTRACTION", "true").lower() == "true"
        
        return GroqConfig(
            api_key=api_key,
            default_model=default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            daily_budget_limit=float(daily_budget) if daily_budget else None,
            monthly_budget_limit=float(monthly_budget) if monthly_budget else None,
            enable_semantic_search=enable_semantic_search,
            enable_llm_reasoning=enable_llm_reasoning,
            enable_conversational_clarification=enable_conversational_clarification,
            enable_intent_extraction=enable_intent_extraction
        )
    
    def validate_config(self) -> bool:
        """Validate the configuration."""
        errors = []
        
        # Check API key
        if not self.config.api_key:
            errors.append("GROQ_API_KEY environment variable is required")
        
        # Check model availability
        if self.config.default_model not in self.config.available_models:
            errors.append(f"Default model {self.config.default_model} not in available models")
        
        # Check cost configuration
        for model in self.config.available_models:
            if model not in self.config.cost_per_1k_tokens:
                errors.append(f"Cost not defined for model {model}")
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True
    
    def get_model_cost(self, model: str, tokens_used: int) -> float:
        """Calculate cost for using a model."""
        if model not in self.config.cost_per_1k_tokens:
            return 0.0
        
        cost_per_token = self.config.cost_per_1k_tokens[model] / 1000
        return cost_per_token * tokens_used
    
    def check_budget_limits(self, model: str, tokens_used: int) -> bool:
        """Check if usage would exceed budget limits."""
        if not self.config.daily_budget_limit and not self.config.monthly_budget_limit:
            return True
        
        cost = self.get_model_cost(model, tokens_used)
        
        # Load current usage
        usage_file = "data/budget_usage.json"
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(usage_file), exist_ok=True)
        
        usage_data = {"daily_spend": 0.0, "monthly_spend": 0.0}
        if os.path.exists(usage_file):
            try:
                with open(usage_file, 'r') as f:
                    usage_data = json.load(f)
            except json.JSONDecodeError:
                pass
                
        # Check against limits
        if self.config.daily_budget_limit and (usage_data["daily_spend"] + cost) > self.config.daily_budget_limit:
            return False
            
        if self.config.monthly_budget_limit and (usage_data["monthly_spend"] + cost) > self.config.monthly_budget_limit:
            return False
            
        # Update usage (assuming the cost is incurred if we checked and passed)
        # Note: In a real system you'd only record usage AFTER the successful API call.
        # This is simplified for the capstone.
        usage_data["daily_spend"] += cost
        usage_data["monthly_spend"] += cost
        
        try:
            with open(usage_file, 'w') as f:
                json.dump(usage_data, f)
        except Exception:
            pass
            
        return True
    
    def get_model_settings(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get model-specific settings."""
        target_model = model or self.config.default_model
        
        return {
            "model": target_model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "cost_per_1k_tokens": self.config.cost_per_1k_tokens.get(target_model, 0.0)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "api_key_set": bool(self.config.api_key),
            "default_model": self.config.default_model,
            "available_models": self.config.available_models,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "daily_budget_limit": self.config.daily_budget_limit,
            "monthly_budget_limit": self.config.monthly_budget_limit,
            "enable_fallback": self.config.enable_fallback,
            "enable_semantic_search": self.config.enable_semantic_search,
            "enable_llm_reasoning": self.config.enable_llm_reasoning,
            "enable_conversational_clarification": self.config.enable_conversational_clarification,
            "enable_intent_extraction": self.config.enable_intent_extraction,
            "environment": self.environment.value
        }
    
    def save_config(self, filepath: str):
        """Save configuration to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def load_config(self, filepath: str):
        """Load configuration from a JSON file."""
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        
        # Update config with loaded data
        for key, value in config_data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> GroqConfig:
    """Get the global configuration."""
    return config_manager.config


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager."""
    return config_manager


def validate_configuration() -> bool:
    """Validate the global configuration."""
    return config_manager.validate_config()


def check_budget(model: str, tokens_used: int) -> bool:
    """Check budget limits using global configuration."""
    return config_manager.check_budget_limits(model, tokens_used)


def get_model_cost(model: str, tokens_used: int) -> float:
    """Get model cost using global configuration."""
    return config_manager.get_model_cost(model, tokens_used)