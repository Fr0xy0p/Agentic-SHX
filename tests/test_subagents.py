"""Unit tests for SubagentManager and InvokeSubagentTool."""

from typing import List, Dict, Any, Optional, Callable
from agentic_shx.providers.base import BaseProvider, ProviderResponse, ToolCall
from agentic_shx.tools.registry import ToolRegistry
from agentic_shx.subagents.manager import SubagentManager
from agentic_shx.subagents.tools import InvokeSubagentTool

class MockSubagentProvider(BaseProvider):
    def __init__(self):
        super().__init__(model="mock-sub-model")

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        on_thought_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResponse:
        return ProviderResponse(
            content="Research completed: found 3 relevant architectural modules."
        )

def test_subagent_invocation(tmp_path):
    provider = MockSubagentProvider()
    base_reg = ToolRegistry.create_default(cwd=str(tmp_path))
    mgr = SubagentManager(provider=provider, base_registry=base_reg, cwd=str(tmp_path))
    tool = InvokeSubagentTool(manager=mgr)

    res = tool.execute(
        type_name="research",
        role="Architecture Inspector",
        prompt="Find where config is loaded"
    )

    assert res.success is True
    assert "Research completed" in res.output
    assert "Architecture Inspector" in res.output

