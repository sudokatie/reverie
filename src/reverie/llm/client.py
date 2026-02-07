"""Abstract LLM client interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class LLMResponse:
    """Response from an LLM."""
    text: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return self.error is None


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, context: Optional[dict] = None) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send
            context: Optional context dict with system prompt, temperature, etc.
            
        Returns:
            LLMResponse with the result
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name."""
        pass


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(self, responses: Optional[list[str]] = None):
        """Initialize with optional canned responses."""
        self.responses = responses or ["This is a mock response."]
        self.call_count = 0
        self.prompts_received: list[str] = []
        self._available = True
    
    def generate(self, prompt: str, context: Optional[dict] = None) -> LLMResponse:
        """Return next canned response."""
        self.prompts_received.append(prompt)
        response_idx = self.call_count % len(self.responses)
        self.call_count += 1
        return LLMResponse(
            text=self.responses[response_idx],
            tokens_used=len(prompt.split()) + len(self.responses[response_idx].split()),
        )
    
    def is_available(self) -> bool:
        """Check mock availability."""
        return self._available
    
    def set_available(self, available: bool) -> None:
        """Set availability for testing."""
        self._available = available
    
    @property
    def model_name(self) -> str:
        """Mock model name."""
        return "mock-model"
