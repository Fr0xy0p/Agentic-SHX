"""Base tool interfaces and registry."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ToolResult:
    """Result returned by a tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_llm_content(self) -> str:
        """Format the result as content returned to the LLM."""
        if self.success:
            return self.output
        return f"Error: {self.error}\nOutput: {self.output}" if self.output else f"Error: {self.error}"


class BaseTool(ABC):
    """Abstract base class for all tools."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema for arguments

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool synchronously."""
        pass

    def to_function_declaration(self) -> Dict[str, Any]:
        """Convert to standard OpenAI/Gemini/Anthropic function declaration schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }
