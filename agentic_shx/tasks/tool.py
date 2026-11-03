"""Tool for managing background processes."""

from typing import Optional, Dict, Any
from agentic_shx.tools.base import BaseTool, ToolResult
from agentic_shx.tasks.manager import TaskManager

class ManageTaskTool(BaseTool):
    """Manages background tasks (list, status, send_input, kill)."""

    name = "manage_task"
    description = (
        "Manage background tasks in the session. Use 'list' to see running tasks, "
        "'status' to view logs of a specific task, 'send_input' to deliver stdin, or 'kill' to stop a task."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "status", "send_input", "kill"],
                "description": "The action to perform."
            },
            "task_id": {
                "type": "string",
                "description": "The TaskId to inspect, kill, or message (required for status, send_input, kill)."
            },
            "input": {
                "type": "string",
                "description": "Input text to deliver to the task (required for send_input)."
            }
        },
        "required": ["action"]
    }

    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager

    def execute(self, action: str, task_id: Optional[str] = None, input: Optional[str] = None, **kwargs) -> ToolResult:
        act = action.lower()
        if act == "list":
            return ToolResult(success=True, output=self.task_manager.list_tasks())
        elif act == "status":
            if not task_id:
                return ToolResult(success=False, output="", error="task_id is required for action='status'.")
            return ToolResult(success=True, output=self.task_manager.get_status(task_id))
        elif act == "send_input":
            if not task_id or input is None:
                return ToolResult(success=False, output="", error="task_id and input are required for action='send_input'.")
            return ToolResult(success=True, output=self.task_manager.send_input(task_id, input))
        elif act == "kill":
            if not task_id:
                return ToolResult(success=False, output="", error="task_id is required for action='kill'.")
            return ToolResult(success=True, output=self.task_manager.kill(task_id))
        else:
            return ToolResult(success=False, output="", error=f"Unknown action '{action}'. Valid: list, status, send_input, kill.")

