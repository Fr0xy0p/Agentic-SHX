"""Git inspection and diff tools."""

import subprocess
import os
from typing import Optional
from agentic_shx.tools.base import BaseTool, ToolResult

class GitDiffTool(BaseTool):
    """Inspects uncommitted changes in git."""

    name = "git_diff"
    description = "View uncommitted git diffs (staged or unstaged) in the repository."
    parameters = {
        "type": "object",
        "properties": {
            "staged": {
                "type": "boolean",
                "description": "If true, show staged changes (git diff --cached). Default false."
            },
            "file_path": {
                "type": "string",
                "description": "Optional specific file path to limit diff to."
            }
        }
    }

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = cwd or os.getcwd()

    def execute(self, staged: bool = False, file_path: Optional[str] = None, **kwargs) -> ToolResult:
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--cached")
        if file_path:
            cmd.extend(["--", file_path])

        try:
            res = subprocess.run(cmd, cwd=self.cwd, capture_output=True, text=True, timeout=30)
            if res.returncode != 0:
                return ToolResult(success=False, output="", error=res.stderr or "Git diff failed.")
            diff_text = res.stdout
            if not diff_text.strip():
                return ToolResult(success=True, output="(No uncommitted changes detected)")
            return ToolResult(success=True, output=diff_text)
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Git diff error: {str(e)}")


class GitStatusTool(BaseTool):
    """Inspects git repository status."""

    name = "git_status"
    description = "Show the working tree status (branch, modified, untracked files)."
    parameters = {"type": "object", "properties": {}}

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = cwd or os.getcwd()

    def execute(self, **kwargs) -> ToolResult:
        try:
            res = subprocess.run(
                ["git", "status", "--short", "--branch"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=15
            )
            if res.returncode != 0:
                return ToolResult(success=False, output="", error=res.stderr or "Git status failed.")
            output = res.stdout.strip()
            return ToolResult(success=True, output=output or "(Clean working tree)")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Git status error: {str(e)}")
