"""Subagent hierarchy and task delegation system."""

import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path

from agentic_shx.providers.base import BaseProvider
from agentic_shx.tools.registry import ToolRegistry
from agentic_shx.safety.permissions import PermissionManager
from agentic_shx.agent.context import ConversationContext
from agentic_shx.agent.loop import AgentLoop

@dataclass
class SubagentType:
    name: str
    description: str
    system_prompt: str
    enable_write_tools: bool = False

RESEARCH_SYSTEM_PROMPT = """You are a specialized Research Subagent.
Your role is to deeply explore the codebase, read relevant files, search for symbols and keywords,
and understand the architecture without modifying any files.
Return a clear, structured summary of your findings to the parent agent."""

PLANNER_SYSTEM_PROMPT = """You are a specialized Planning Subagent.
Your role is to analyze the user's objective, break it down into clean, sequential implementation phases,
identify risks, and provide actionable milestones for the primary coding agent."""


class SubagentManager:
    """Oversees subagent creation, isolated execution, and message delivery."""

    def __init__(self, provider: BaseProvider, base_registry: ToolRegistry, cwd: str):
        self.provider = provider
        self.base_registry = base_registry
        self.cwd = cwd
        self.custom_types: Dict[str, SubagentType] = {
            "research": SubagentType(
                name="research",
                description="Read-only research subagent for exploring codebase and finding files",
                system_prompt=RESEARCH_SYSTEM_PROMPT,
                enable_write_tools=False
            ),
            "planner": SubagentType(
                name="planner",
                description="Planning subagent for decomposing complex objectives",
                system_prompt=PLANNER_SYSTEM_PROMPT,
                enable_write_tools=False
            ),
            "self": SubagentType(
                name="self",
                description="Full-capability subagent with same configuration as parent",
                system_prompt="You are a child coding agent assisting the primary agent with a delegated task.",
                enable_write_tools=True
            ),
        }
        self.active_subagents: Dict[str, Dict[str, Any]] = {}

    def define_type(self, name: str, description: str, system_prompt: str, enable_write_tools: bool = False) -> str:
        self.custom_types[name] = SubagentType(
            name=name,
            description=description,
            system_prompt=system_prompt,
            enable_write_tools=enable_write_tools
        )
        return f"Subagent type '{name}' defined successfully."

    def invoke(
        self,
        type_name: str,
        role: str,
        prompt: str,
        on_subagent_event: Optional[Callable[[str, str], None]] = None
    ) -> str:
        """Runs a subagent synchronously in an isolated loop and returns its findings."""
        sub_type = self.custom_types.get(type_name) or self.custom_types.get("self")
        sub_id = f"sub-{uuid.uuid4().hex[:6]}"

        # Setup isolated tool registry for this subagent
        sub_registry = ToolRegistry()
        for tool in self.base_registry.list_tools():
            # If not write-enabled, exclude mutating tools
            if not sub_type.enable_write_tools and tool.name in ("write_file", "edit_file"):
                continue
            sub_registry.register(tool)

        # Isolated context & permissions
        sub_context = ConversationContext(
            system_prompt=f"{sub_type.system_prompt}\nRole: {role}\nWorkspace: {self.cwd}"
        )
        sub_permissions = PermissionManager(auto_approve_safe=True)

        self.active_subagents[sub_id] = {
            "type": type_name,
            "role": role,
            "status": "RUNNING"
        }

        if on_subagent_event:
            on_subagent_event(sub_id, f"Spawned subagent [{role}] ({type_name})")

        sub_loop = AgentLoop(
            provider=self.provider,
            tool_registry=sub_registry,
            context=sub_context,
            permission_manager=sub_permissions,
            max_steps=15
        )

        try:
            result = sub_loop.step(prompt)
            self.active_subagents[sub_id]["status"] = "COMPLETED"
            if on_subagent_event:
                on_subagent_event(sub_id, f"Subagent [{role}] completed its task.")
            return f"[Subagent '{role}' ({sub_id}) Report]:\n{result}"
        except Exception as e:
            self.active_subagents[sub_id]["status"] = "FAILED"
            return f"[Subagent '{role}' Failed]: {str(e)}"
