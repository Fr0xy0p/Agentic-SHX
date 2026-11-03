"""Bash / shell execution tool."""

import subprocess
import os
from typing import Dict, Any, Optional
from agentic_shx.tools.base import BaseTool, ToolResult

class BashTool(BaseTool):
    """Executes shell commands with timeout and output capture."""

    name = "bash"
    description = (
        "Run a shell command in the terminal. Use this to run tests, git commands, "
        "builds, install packages, and inspect system state. The command executes "
        "in the project root directory unless changed."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The exact shell command line string to execute."
            },
            "timeout": {
                "type": "integer",
                "description": "Optional timeout in seconds. Defaults to 120."
            }
        },
        "required": ["command"]
    }

    def __init__(self, cwd: Optional[str] = None, max_output_chars: int = 8000, default_timeout: int = 120):
        self.cwd = cwd or os.getcwd()
        self.max_output_chars = max_output_chars
        self.default_timeout = default_timeout

    def execute(self, command: str, timeout: Optional[int] = None, **kwargs) -> ToolResult:
        actual_timeout = timeout or self.default_timeout
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=actual_timeout,
                executable="/bin/bash" if os.path.exists("/bin/bash") else None
            )
            
            stdout = process.stdout
            stderr = process.stderr
            exit_code = process.returncode

            combined = ""
            if stdout:
                combined += stdout
            if stderr:
                if combined:
                    combined += "\n--- STDERR ---\n"
                combined += stderr

            # Truncate if output exceeds threshold
            truncated = False
            total_chars = len(combined)
            if total_chars > self.max_output_chars:
                truncated = True
                half = self.max_output_chars // 2
                combined = (
                    combined[:half]
                    + f"\n\n[... Output truncated ({total_chars} total characters) ...]\n\n"
                    + combined[-half:]
                )

            metadata = {
                "exit_code": exit_code,
                "command": command,
                "truncated": truncated
            }

            if exit_code == 0:
                output_str = combined if combined.strip() else "(Command executed with code 0 and no output)"
                return ToolResult(success=True, output=output_str, metadata=metadata)
            else:
                return ToolResult(
                    success=False,
                    output=combined,
                    error=f"Command exited with non-zero exit code {exit_code}",
                    metadata=metadata
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {actual_timeout} seconds."
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}"
            )
