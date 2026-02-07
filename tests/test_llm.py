"""Tests for LLM integration."""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

from reverie.llm import (
    LLMClient,
    LLMResponse,
    MockLLMClient,
    OllamaClient,
    OpenAIClient,
    create_client,
    generate,
    build_scene_prompt,
    build_dialogue_prompt,
    build_generation_prompt,
    parse_generation_response,
)


class TestLLMResponse:
    """Tests for LLMResponse."""

    def test_success_response(self):
        """Successful response."""
        resp = LLMResponse(text="Hello", tokens_used=10)
        assert resp.success
        assert resp.text == "Hello"

    def test_error_response(self):
        """Error response."""
        resp = LLMResponse(text="", error="Connection failed")
        assert not resp.success
        assert resp.error == "Connection failed"


class TestMockLLMClient:
    """Tests for MockLLMClient."""

    def test_returns_canned_response(self):
        """Mock returns canned responses."""
        client = MockLLMClient(responses=["Response 1", "Response 2"])
        
        r1 = client.generate("Prompt 1")
        assert r1.text == "Response 1"
        
        r2 = client.generate("Prompt 2")
        assert r2.text == "Response 2"

    def test_cycles_responses(self):
        """Mock cycles through responses."""
        client = MockLLMClient(responses=["A", "B"])
        
        assert client.generate("1").text == "A"
        assert client.generate("2").text == "B"
        assert client.generate("3").text == "A"  # Cycles back

    def test_tracks_prompts(self):
        """Mock tracks received prompts."""
        client = MockLLMClient()
        client.generate("First prompt")
        client.generate("Second prompt")
        
        assert len(client.prompts_received) == 2
        assert "First" in client.prompts_received[0]

    def test_availability(self):
        """Mock availability can be toggled."""
        client = MockLLMClient()
        assert client.is_available()
        
        client.set_available(False)
        assert not client.is_available()


class TestOllamaClient:
    """Tests for OllamaClient (mocked)."""

    def test_init_defaults(self):
        """Initialize with defaults."""
        client = OllamaClient()
        assert client.model == "llama2"
        assert client.endpoint == "http://localhost:11434"

    def test_init_custom(self):
        """Initialize with custom settings."""
        client = OllamaClient(
            model="mistral",
            endpoint="http://custom:8080",
            timeout=60.0,
        )
        assert client.model == "mistral"
        assert client.endpoint == "http://custom:8080"

    @patch("reverie.llm.ollama.httpx.Client")
    def test_generate_success(self, mock_client_class):
        """Successful generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": "Generated text",
            "eval_count": 50,
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OllamaClient()
        result = client.generate("Test prompt")
        
        assert result.success
        assert result.text == "Generated text"
        assert result.tokens_used == 50

    @patch("reverie.llm.ollama.httpx.Client")
    def test_generate_timeout(self, mock_client_class):
        """Handle timeout error."""
        import httpx
        
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value = mock_client
        
        client = OllamaClient()
        result = client.generate("Test")
        
        assert not result.success
        assert "timed out" in result.error.lower()


class TestOpenAIClient:
    """Tests for OpenAIClient (mocked)."""

    def test_init_no_key_error(self):
        """Generate fails without API key."""
        client = OpenAIClient(api_key="")
        result = client.generate("Test")
        
        assert not result.success
        assert "API key" in result.error

    @patch("reverie.llm.openai.httpx.Client")
    def test_generate_success(self, mock_client_class):
        """Successful generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response"}, "finish_reason": "stop"}],
            "usage": {"total_tokens": 100},
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = OpenAIClient(api_key="test-key")
        result = client.generate("Test prompt")
        
        assert result.success
        assert result.text == "AI response"
        assert result.tokens_used == 100


class TestCreateClient:
    """Tests for create_client factory."""

    def test_create_mock(self):
        """Create mock client."""
        @dataclass
        class Config:
            provider: str = "mock"
            responses: list = None
        
        client = create_client(Config(responses=["Test"]))
        assert isinstance(client, MockLLMClient)

    def test_create_ollama(self):
        """Create Ollama client."""
        @dataclass
        class Config:
            provider: str = "ollama"
            model: str = "codellama"
            endpoint: str = None
            timeout: float = 30.0
        
        client = create_client(Config())
        assert isinstance(client, OllamaClient)
        assert client.model == "codellama"

    def test_create_openai(self):
        """Create OpenAI client."""
        @dataclass
        class Config:
            provider: str = "openai"
            model: str = "gpt-4"
            api_key: str = "test-key"
            endpoint: str = None
            timeout: float = 30.0
        
        client = create_client(Config())
        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4"


class TestGenerate:
    """Tests for generate helper."""

    def test_generate_success(self):
        """Generate returns text on success."""
        client = MockLLMClient(responses=["Generated content"])
        result = generate(client, "Prompt")
        assert result == "Generated content"

    def test_generate_error(self):
        """Generate returns empty on error."""
        client = MockLLMClient()
        client._available = False
        # Mock to return error
        original_generate = client.generate
        def error_generate(prompt, context=None):
            return LLMResponse(text="", error="Failed")
        client.generate = error_generate
        
        result = generate(client, "Prompt")
        assert result == ""


class TestPromptBuilding:
    """Tests for prompt building functions."""

    def test_build_scene_prompt(self):
        """Build scene narration prompt."""
        @dataclass
        class Location:
            name: str = "Dark Forest"
            description: str = "Trees block the sunlight."
        
        prompt = build_scene_prompt(Location(), "look around")
        
        assert "Dark Forest" in prompt
        assert "look around" in prompt

    def test_build_scene_prompt_with_context(self):
        """Build scene prompt with full context."""
        @dataclass
        class Location:
            name: str = "Tavern"
            description: str = ""
        
        @dataclass
        class Character:
            name: str = "Hero"
        
        @dataclass
        class NPC:
            name: str = "Bartender"
        
        context = {
            "character": Character(),
            "npcs": [NPC()],
            "history": ["Entered tavern", "Ordered drink"],
        }
        
        prompt = build_scene_prompt(Location(), "ask about rumors", context)
        
        assert "Tavern" in prompt
        assert "Hero" in prompt
        assert "Bartender" in prompt
        assert "rumors" in prompt

    def test_build_dialogue_prompt(self):
        """Build NPC dialogue prompt."""
        @dataclass
        class NPC:
            name: str = "Guard"
            occupation: str = "city guard"
            traits: list = None
            disposition: str = "neutral"
            motivation: str = ""
            
            def __post_init__(self):
                self.traits = ["stern", "dutiful"]
        
        prompt = build_dialogue_prompt(NPC(), "Can I pass?")
        
        assert "Guard" in prompt
        assert "city guard" in prompt
        assert "Can I pass?" in prompt

    def test_build_generation_prompt_npc(self):
        """Build NPC generation prompt."""
        prompt = build_generation_prompt("npc", {"race": "elf", "occupation": "mage"})
        
        assert "elf" in prompt
        assert "mage" in prompt
        assert "JSON" in prompt

    def test_build_generation_prompt_quest(self):
        """Build quest generation prompt."""
        prompt = build_generation_prompt("quest", {"difficulty": "hard"})
        
        assert "hard" in prompt
        assert "objective" in prompt


class TestParseResponse:
    """Tests for response parsing."""

    def test_parse_json_direct(self):
        """Parse direct JSON response."""
        response = '{"name": "Test", "value": 42}'
        result = parse_generation_response(response)
        
        assert result["name"] == "Test"
        assert result["value"] == 42

    def test_parse_json_in_text(self):
        """Parse JSON embedded in text."""
        response = 'Here is the data: {"name": "Embedded"} and more text.'
        result = parse_generation_response(response)
        
        assert result["name"] == "Embedded"

    def test_parse_json_code_block(self):
        """Parse JSON in code block."""
        response = '```json\n{"name": "CodeBlock"}\n```'
        result = parse_generation_response(response)
        
        assert result["name"] == "CodeBlock"

    def test_parse_invalid_json(self):
        """Return empty dict for invalid JSON."""
        response = "This is not JSON at all."
        result = parse_generation_response(response)
        
        assert result == {}
