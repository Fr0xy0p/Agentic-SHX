"""Central registry for discovering and executing tools."""

from typing import Dict, List, Any, Optional
from agentic_shx.tools.base import BaseTool, ToolResult
from agentic_shx.tools.bash import BashTool
from agentic_shx.tools.file_ops import ReadFileTool, WriteFileTool, EditFileTool
from agentic_shx.tools.search import SearchFilesTool, ListFilesTool
from agentic_shx.tools.git_ops import GitDiffTool, GitStatusTool

class ToolRegistry:
    """Manages all available tools in Agentic-SHX."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_declarations(self) -> List[Dict[str, Any]]:
        """Return function calling declarations formatted for LLMs."""
        return [tool.to_function_declaration() for tool in self._tools.values()]

    def execute(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' is not registered. Available tools: {list(self._tools.keys())}"
            )
        try:
            return tool.execute(**arguments)
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{name}' raised unexpected exception: {str(e)}"
            )

    @classmethod
    def create_default(cls, cwd: Optional[str] = None) -> "ToolRegistry":
        """Instantiate and register all built-in tools for a workspace."""
        registry = cls()
        registry.register(BashTool(cwd=cwd))
        registry.register(ReadFileTool(cwd=cwd))
        registry.register(WriteFileTool(cwd=cwd))
        registry.register(EditFileTool(cwd=cwd))
        registry.register(SearchFilesTool(cwd=cwd))
        registry.register(ListFilesTool(cwd=cwd))
        registry.register(GitDiffTool(cwd=cwd))
        registry.register(GitStatusTool(cwd=cwd))
        return registry
