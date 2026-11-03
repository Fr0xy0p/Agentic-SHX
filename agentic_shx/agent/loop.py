"""Autonomous ReAct Agent Loop with Antigravity step orchestration."""

from typing import Callable, Optional, Any
from agentic_shx.agent.context import ConversationContext
from agentic_shx.providers.base import BaseProvider, ProviderResponse, ToolCall
from agentic_shx.tools.registry import ToolRegistry
from agentic_shx.safety.permissions import PermissionManager, ApprovalChoice, RiskLevel

class AgentLoop:
    """Manages the autonomous execution cycle between user, LLM, and tools."""

    def __init__(
        self,
        provider: BaseProvider,
        tool_registry: ToolRegistry,
        context: ConversationContext,
        permission_manager: PermissionManager,
        max_steps: int = 30,
        temperature: float = 0.2,
        session_manager: Optional[Any] = None,
        artifact_manager: Optional[Any] = None,
        on_step_start: Optional[Callable[[int, int], None]] = None,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        on_thought_chunk: Optional[Callable[[str], None]] = None,
        on_tool_start: Optional[Callable[[ToolCall], None]] = None,
        on_tool_finish: Optional[Callable[[ToolCall, str, bool], None]] = None,
        on_artifact_created: Optional[Callable[[Any], None]] = None,
        on_request_approval: Optional[Callable[[str, dict, RiskLevel, str], ApprovalChoice]] = None,
    ):
        self.provider = provider
        self.tool_registry = tool_registry
        self.context = context
        self.permission_manager = permission_manager
        self.max_steps = max_steps
        self.temperature = temperature
        self.session_manager = session_manager
        self.artifact_manager = artifact_manager
        
        # UI Callbacks
        self.on_step_start = on_step_start
        self.on_content_chunk = on_content_chunk
        self.on_thought_chunk = on_thought_chunk
        self.on_tool_start = on_tool_start
        self.on_tool_finish = on_tool_finish
        self.on_artifact_created = on_artifact_created
        self.on_request_approval = on_request_approval

    def step(self, user_message: str) -> str:
        """
        Execute one full multi-step autonomous conversation turn.
        Returns the final response text.
        """
        self.context.add_user_message(user_message)
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1

            if self.on_step_start:
                self.on_step_start(current_step, self.max_steps)

            # Check context token compaction if history is getting deep
            if self.context.estimate_tokens() > 30_000:
                self.context.compact_history()

            tools_schema = self.tool_registry.get_declarations()
            messages = self.context.get_messages_for_llm()

            # Call provider
            try:
                response: ProviderResponse = self.provider.generate(
                    messages=messages,
                    tools=tools_schema,
                    temperature=self.temperature,
                    on_content_chunk=self.on_content_chunk,
                    on_thought_chunk=self.on_thought_chunk,
                )
            except Exception as e:
                err_msg = f"LLM Generation failed: {str(e)}"
                if self.session_manager:
                    self.session_manager.log_event("ERROR", err_msg)
                return err_msg

            # Log model response to session transcript
            if self.session_manager:
                if response.thinking:
                    self.session_manager.log_event("MODEL_THINKING", response.thinking)
                self.session_manager.log_event(
                    "MODEL_OUTPUT",
                    response.content,
                    {"tool_calls_count": len(response.tool_calls)}
                )

            # Record model response into trajectory
            self.context.add_assistant_message(
                content=response.content,
                tool_calls=response.tool_calls if response.has_tool_calls else None
            )

            # If no tools invoked, turn is complete!
            if not response.has_tool_calls:
                return response.content

            # Process each requested tool call
            aborted = False
            for tc in response.tool_calls:
                if self.session_manager:
                    self.session_manager.log_event("TOOL_CALL", {"id": tc.id, "name": tc.name, "arguments": tc.arguments})

                if self.on_tool_start:
                    self.on_tool_start(tc)

                # Check safety and permissions
                needs_approval, risk, reason = self.permission_manager.should_ask_permission(
                    tc.name, tc.arguments
                )

                if needs_approval and self.on_request_approval:
                    choice = self.on_request_approval(tc.name, tc.arguments, risk, reason)
                    if choice == ApprovalChoice.ABORT:
                        self.context.add_tool_result(tc.id, tc.name, "Operation aborted by user.")
                        aborted = True
                        break
                    elif choice == ApprovalChoice.NO:
                        self.context.add_tool_result(tc.id, tc.name, "Execution denied by user.")
                        if self.on_tool_finish:
                            self.on_tool_finish(tc, "User denied permission", False)
                        continue
                    elif choice == ApprovalChoice.ALWAYS:
                        self.permission_manager.record_session_allow(tc.name, tc.arguments)

                # Execute tool
                result = self.tool_registry.execute(tc.name, tc.arguments)
                tool_output_for_llm = result.to_llm_content()

                if self.session_manager:
                    self.session_manager.log_event("TOOL_RESULT", {
                        "id": tc.id,
                        "name": tc.name,
                        "success": result.success,
                        "output": result.output[:1000] if result.output else ""
                    })

                if self.on_tool_finish:
                    self.on_tool_finish(tc, result.output or result.error or "", result.success)

                # Check if an artifact was created
                if tc.name == "create_artifact" and self.artifact_manager:
                    filename = tc.arguments.get("filename", "")
                    art = self.artifact_manager.get_artifact(filename)
                    if art and self.on_artifact_created:
                        self.on_artifact_created(art)

                # Record observation
                self.context.add_tool_result(tc.id, tc.name, tool_output_for_llm)

            if aborted:
                return "Autonomous execution aborted by user."

        return "Reached maximum autonomous step limit without completion."
