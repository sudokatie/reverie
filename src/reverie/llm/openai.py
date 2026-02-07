"""OpenAI LLM client."""

import os
from typing import Optional
import httpx

from .client import LLMClient, LLMResponse


class OpenAIClient(LLMClient):
    """Client for OpenAI API."""
    
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_ENDPOINT = "https://api.openai.com/v1"
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = 30.0,
    ):
        """Initialize OpenAI client.
        
        Args:
            model: Model name (e.g., 'gpt-3.5-turbo', 'gpt-4')
            api_key: API key (or set OPENAI_API_KEY env var)
            endpoint: API endpoint URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
    
    def generate(self, prompt: str, context: Optional[dict] = None) -> LLMResponse:
        """Generate a response from OpenAI.
        
        Args:
            prompt: The prompt to send
            context: Optional context with 'system', 'temperature', etc.
            
        Returns:
            LLMResponse with the result
        """
        if not self.api_key:
            return LLMResponse(
                text="",
                error="No API key provided",
            )
        
        context = context or {}
        
        messages = []
        if "system" in context:
            messages.append({"role": "system", "content": context["system"]})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
        }
        
        if "temperature" in context:
            payload["temperature"] = context["temperature"]
        
        if "max_tokens" in context:
            payload["max_tokens"] = context["max_tokens"]
        
        try:
            response = self._client.post(
                f"{self.endpoint}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = data.get("usage", {})
            
            return LLMResponse(
                text=message.get("content", ""),
                tokens_used=usage.get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
            )
        except httpx.TimeoutException:
            return LLMResponse(
                text="",
                error="Request timed out",
            )
        except httpx.HTTPStatusError as e:
            return LLMResponse(
                text="",
                error=f"HTTP error: {e.response.status_code}",
            )
        except Exception as e:
            return LLMResponse(
                text="",
                error=str(e),
            )
    
    def is_available(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self.api_key:
            return False
        try:
            response = self._client.get(
                f"{self.endpoint}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.status_code == 200
        except Exception:
            return False
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.model
