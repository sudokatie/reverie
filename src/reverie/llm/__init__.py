"""LLM integration for Reverie."""

from typing import Optional, Any

from .client import LLMClient, LLMResponse, MockLLMClient
from .ollama import OllamaClient
from .openai import OpenAIClient
from .prompts import (
    DM_SYSTEM_PROMPT,
    GENERATION_SYSTEM_PROMPT,
    build_scene_prompt,
    build_dialogue_prompt,
    build_generation_prompt,
    parse_generation_response,
)


def create_client(config: Any) -> LLMClient:
    """Create an LLM client based on configuration.
    
    Args:
        config: Configuration object with provider, model, endpoint, etc.
        
    Returns:
        Configured LLM client
    """
    provider = getattr(config, "provider", "ollama")
    model = getattr(config, "model", None)
    endpoint = getattr(config, "endpoint", None)
    timeout = getattr(config, "timeout", 30.0)
    api_key = getattr(config, "api_key", None)
    
    if provider == "openai":
        kwargs = {"timeout": timeout}
        if model:
            kwargs["model"] = model
        if endpoint:
            kwargs["endpoint"] = endpoint
        if api_key:
            kwargs["api_key"] = api_key
        return OpenAIClient(**kwargs)
    
    elif provider == "ollama":
        kwargs = {"timeout": timeout}
        if model:
            kwargs["model"] = model
        if endpoint:
            kwargs["endpoint"] = endpoint
        return OllamaClient(**kwargs)
    
    elif provider == "mock":
        responses = getattr(config, "responses", None)
        return MockLLMClient(responses=responses)
    
    else:
        # Default to Ollama
        return OllamaClient()


def generate(
    client: LLMClient,
    prompt: str,
    context: Optional[dict] = None,
) -> str:
    """Generate text from an LLM client.
    
    Args:
        client: The LLM client
        prompt: The prompt
        context: Optional context
        
    Returns:
        Generated text (empty string on error)
    """
    response = client.generate(prompt, context)
    if response.success:
        return response.text
    return ""


__all__ = [
    "LLMClient",
    "LLMResponse",
    "MockLLMClient",
    "OllamaClient",
    "OpenAIClient",
    "create_client",
    "generate",
    "DM_SYSTEM_PROMPT",
    "GENERATION_SYSTEM_PROMPT",
    "build_scene_prompt",
    "build_dialogue_prompt",
    "build_generation_prompt",
    "parse_generation_response",
]
