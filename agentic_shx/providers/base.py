"""Abstract LLM Provider interface and common data structures."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

@dataclass
class ToolCall:
    """Represents a function/tool invocation from the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]

@dataclass
class ProviderResponse:
    """Standardized response from any LLM provider."""
    content: str = ""
    thinking: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw_response: Dict[str, Any] = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseProvider(ABC):
    """Abstract base class for all LLM backends."""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        on_thought_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResponse:
        """
        Generate completion, streaming chunks to callbacks if provided.
        Returns final structured ProviderResponse.
        """
        pass

