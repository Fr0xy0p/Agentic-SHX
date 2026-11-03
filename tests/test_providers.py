"""Unit tests for provider resolution and Groq integration."""

import os
import pytest
from agentic_shx.providers.factory import get_provider
from agentic_shx.providers.groq_provider import GroqProvider
from agentic_shx.providers.gemini_provider import GeminiProvider
from agentic_shx.providers.claude_provider import ClaudeProvider
from agentic_shx.providers.openai_provider import OpenAIProvider

def test_groq_provider_instantiation():
    provider = get_provider(
        model="groq/llama-3.3-70b-versatile",
        api_key="gsk_dummy_key"
    )
    assert isinstance(provider, GroqProvider)
    assert provider.model == "llama-3.3-70b-versatile"
    assert provider.api_key == "gsk_dummy_key"
    assert provider.base_url == "https://api.groq.com/openai/v1"

def test_groq_provider_env_var(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_env_test_12345")
    provider = get_provider(model="groq/deepseek-r1-distill-llama-70b")
    assert isinstance(provider, GroqProvider)
    assert provider.api_key == "gsk_env_test_12345"
    assert provider.model == "deepseek-r1-distill-llama-70b"

def test_groq_provider_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Groq API key not found"):
        get_provider(model="groq/llama-3.1-8b-instant")

def test_groq_provider_from_config_dict():
    provider = get_provider(
        model="groq/mixtral-8x7b-32768",
        api_keys={"groq": "gsk_from_config"}
    )
    assert isinstance(provider, GroqProvider)
    assert provider.api_key == "gsk_from_config"

def test_other_providers_resolution(monkeypatch):
    # Gemini
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_gemini_key")
    p_gemini = get_provider("gemini/gemini-2.5-flash")
    assert isinstance(p_gemini, GeminiProvider)

    # Claude
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy_claude_key")
    p_claude = get_provider("claude-3-7-sonnet")
    assert isinstance(p_claude, ClaudeProvider)

    # OpenAI / Ollama
    p_ollama = get_provider("ollama/qwen2.5-coder")
    assert isinstance(p_ollama, OpenAIProvider)

