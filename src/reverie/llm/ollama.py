"""Ollama LLM client for local models."""

from typing import Optional
import httpx

from .client import LLMClient, LLMResponse


class OllamaClient(LLMClient):
    """Client for Ollama local LLM server."""
    
    DEFAULT_MODEL = "llama2"
    DEFAULT_ENDPOINT = "http://localhost:11434"
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = 30.0,
    ):
        """Initialize Ollama client.
        
        Args:
            model: Model name (e.g., 'llama2', 'mistral', 'codellama')
            endpoint: Ollama server URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
    
    def generate(self, prompt: str, context: Optional[dict] = None) -> LLMResponse:
        """Generate a response from Ollama.
        
        Args:
            prompt: The prompt to send
            context: Optional context with 'system', 'temperature', etc.
            
        Returns:
            LLMResponse with the result
        """
        context = context or {}
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        if "system" in context:
            payload["system"] = context["system"]
        
        if "temperature" in context:
            payload["options"] = {"temperature": context["temperature"]}
        
        try:
            response = self._client.post(
                f"{self.endpoint}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                text=data.get("response", ""),
                tokens_used=data.get("eval_count", 0),
                finish_reason="stop",
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
        """Check if Ollama server is available."""
        try:
            response = self._client.get(f"{self.endpoint}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.model
    
    def list_models(self) -> list[str]:
        """List available models on the Ollama server."""
        try:
            response = self._client.get(f"{self.endpoint}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception:
            return []
