"""Tests for autonomous ReAct Agent Loop."""

from typing import List, Dict, Any, Optional, Callable
from agentic_shx.providers.base import BaseProvider, ProviderResponse, ToolCall
from agentic_shx.tools.registry import ToolRegistry
from agentic_shx.safety.permissions import PermissionManager
from agentic_shx.agent.context import ConversationContext
from agentic_shx.agent.loop import AgentLoop

class MockProvider(BaseProvider):
    """Mock LLM that returns a tool call on turn 1, and final text on turn 2."""

    def __init__(self):
        super().__init__(model="mock-model")
        self.call_count = 0

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        on_thought_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResponse:
        self.call_count += 1
        if self.call_count == 1:
            # Instruct agent to write a file
            return ProviderResponse(
                content="I will create a greeting file for you.",
                tool_calls=[
                    ToolCall(
                        id="call_1",
                        name="write_file",
                        arguments={"path": "hello.txt", "content": "Hello Autonomous Agent!"}
                    )
                ]
            )
        else:
            # Final completion
            return ProviderResponse(
                content="I have successfully created the file hello.txt with your greeting."
            )

def test_agent_loop_execution(tmp_path):
    mock_provider = MockProvider()
    registry = ToolRegistry.create_default(cwd=str(tmp_path))
    permission_manager = PermissionManager(auto_approve_safe=True)
    context = ConversationContext(system_prompt="Test system prompt")

    loop = AgentLoop(
        provider=mock_provider,
        tool_registry=registry,
        context=context,
        permission_manager=permission_manager,
    )

    result = loop.step("Create a hello.txt file")

    assert "successfully created" in result
    assert mock_provider.call_count == 2
    
    # Verify file was actually created on disk
    created_file = tmp_path / "hello.txt"
    assert created_file.exists()
    assert created_file.read_text() == "Hello Autonomous Agent!"

