"""Tools for invoking and defining subagents."""

from typing import Dict, Any, Optional
from agentic_shx.tools.base import BaseTool, ToolResult
from agentic_shx.subagents.manager import SubagentManager

class InvokeSubagentTool(BaseTool):
    """Tool to spawn an autonomous subagent for delegation."""

    name = "invoke_subagent"
    description = (
        "Launch an autonomous subagent to perform a delegated task in an isolated context. "
        "Built-in types: 'research' (read-only codebase explorer), 'planner' (step-by-step planning), 'self' (full coder). "
        "The subagent performs its task and sends back a complete report."
    )
    parameters = {
        "type": "object",
        "properties": {
            "type_name": {
                "type": "string",
                "enum": ["research", "planner", "self"],
                "description": "Type of subagent to invoke."
            },
            "role": {
                "type": "string",
                "description": "Job title or role description (e.g. 'Codebase Researcher', 'Database Schema Analyst')."
            },
            "prompt": {
                "type": "string",
                "description": "Specific instruction and questions for the subagent to solve."
            }
        },
        "required": ["type_name", "role", "prompt"]
    }

    def __init__(self, manager: SubagentManager):
        self.manager = manager

    def execute(
        self,
        type_name: Optional[str] = None,
        TypeName: Optional[str] = None,
        role: Optional[str] = None,
        Role: Optional[str] = None,
        prompt: Optional[str] = None,
        Prompt: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        t_name = type_name or TypeName or "research"
        r_name = role or Role or "Specialist"
        p_text = prompt or Prompt or ""

        if not p_text:
            return ToolResult(success=False, output="", error="Prompt is required to invoke a subagent.")

        output = self.manager.invoke(type_name=t_name, role=r_name, prompt=p_text)
        return ToolResult(success=True, output=output)


class DefineSubagentTool(BaseTool):
    """Tool to dynamically register a custom subagent type."""

    name = "define_subagent"
    description = "Define a new custom subagent type with specialized system prompt and tool access."
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Unique identifier for this subagent type."},
            "description": {"type": "string", "description": "What this subagent does and when to use it."},
            "system_prompt": {"type": "string", "description": "System prompt for the subagent."},
            "enable_write_tools": {"type": "boolean", "description": "Whether to grant file modification tools."}
        },
        "required": ["name", "description", "system_prompt"]
    }

    def __init__(self, manager: SubagentManager):
        self.manager = manager

    def execute(self, name: str, description: str, system_prompt: str, enable_write_tools: bool = False, **kwargs) -> ToolResult:
        res = self.manager.define_type(name, description, system_prompt, enable_write_tools)
        return ToolResult(success=True, output=res)
