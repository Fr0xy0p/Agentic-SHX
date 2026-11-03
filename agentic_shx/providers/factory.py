"""Factory for resolving and instantiating LLM providers."""

from typing import Optional, Dict
from agentic_shx.providers.base import BaseProvider
from agentic_shx.providers.gemini_provider import GeminiProvider
from agentic_shx.providers.claude_provider import ClaudeProvider
from agentic_shx.providers.openai_provider import OpenAIProvider
from agentic_shx.providers.groq_provider import GroqProvider

def get_provider(
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    api_keys: Optional[Dict[str, str]] = None,
    api_bases: Optional[Dict[str, str]] = None
) -> BaseProvider:
    """Instantiate the appropriate provider based on model name."""
    m = model.lower()
    keys = api_keys or {}
    bases = api_bases or {}

    # Check Gemini
    if "gemini" in m or m.startswith("google/"):
        key = api_key or keys.get("gemini") or keys.get("google")
        return GeminiProvider(model=model, api_key=key, base_url=base_url or bases.get("gemini"))

    # Check Claude
    if "claude" in m or m.startswith("anthropic/"):
        key = api_key or keys.get("anthropic") or keys.get("claude")
        return ClaudeProvider(model=model, api_key=key, base_url=base_url or bases.get("claude"))

    # Check Groq
    if "groq" in m or m.startswith("groq/"):
        key = api_key or keys.get("groq")
        return GroqProvider(model=model, api_key=key, base_url=base_url or bases.get("groq"))

    # Default to OpenAI-compatible (OpenAI, Ollama, OpenRouter, DeepSeek)
    key = api_key or keys.get("openai") or keys.get("openrouter")
    return OpenAIProvider(model=model, api_key=key, base_url=base_url or bases.get("openai"))

