"""Bash and shell execution tool with background task support and directory navigation."""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional
from agentic_shx.tools.base import BaseTool, ToolResult
from agentic_shx.tasks.manager import TaskManager
from agentic_shx.shell_integration import is_shell_state_command, handoff_command_to_shell, copy_to_clipboard

class BashTool(BaseTool):
    """Executes shell commands with timeout, background execution, and output capture."""

    name = "bash"
    description = (
        "Run a shell command in the terminal. Supports synchronous execution, directory navigation (cd), "
        "and backgrounding long-running tasks and servers via wait_ms or is_daemon."
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
                "description": "Optional timeout in seconds for synchronous execution. Defaults to 120."
            },
            "wait_ms": {
                "type": "integer",
                "description": "Milliseconds to wait before backgrounding the command (e.g. 5000). If it exceeds this, it continues running as a background task."
            },
            "is_daemon": {
                "type": "boolean",
                "description": "Set to true for long-running servers/watchers that should immediately run in the background."
            }
        },
        "required": ["command"]
    }

    def __init__(
        self,
        cwd: Optional[str] = None,
        max_output_chars: int = 8000,
        default_timeout: int = 120,
        task_manager: Optional[TaskManager] = None
    ):
        self.cwd = cwd or os.getcwd()
        self.max_output_chars = max_output_chars
        self.default_timeout = default_timeout
        self.task_manager = task_manager

    def execute(
        self,
        command: Optional[str] = None,
        CommandLine: Optional[str] = None,
        timeout: Optional[int] = None,
        wait_ms: Optional[int] = None,
        WaitMsBeforeAsync: Optional[int] = None,
        is_daemon: bool = False,
        IsDaemon: bool = False,
        **kwargs
    ) -> ToolResult:
        cmd = command or CommandLine
        if not cmd:
            return ToolResult(success=False, output="", error="No command provided.")

        actual_wait_ms = wait_ms or WaitMsBeforeAsync
        actual_is_daemon = is_daemon or IsDaemon

        # Handoff to parent shell if it alters shell state (e.g. cd, export, source)
        if is_shell_state_command(cmd):
            handoff_command_to_shell(cmd)
            copy_to_clipboard(cmd)

        # If TaskManager is available and either backgrounding parameter is requested
        if self.task_manager and (actual_is_daemon or actual_wait_ms is not None):
            ms = actual_wait_ms if actual_wait_ms is not None else 5000
            completed_sync, output_text, task = self.task_manager.launch(
                command=cmd,
                cwd=self.cwd,
                is_daemon=actual_is_daemon,
                wait_ms=ms
            )
            if not completed_sync:
                # Backgrounded
                return ToolResult(
                    success=True,
                    output=output_text,
                    metadata={"task_id": task.task_id if task else None, "background": True}
                )
            else:
                return ToolResult(
                    success=task.returncode == 0 if task else True,
                    output=output_text or "(Command finished with code 0 and no output)",
                    metadata={"exit_code": task.returncode if task else 0}
                )

        # Standard synchronous execution
        actual_timeout = timeout or self.default_timeout
        try:
            # If the command changes directory, track the new working directory
            has_cd = any(part in cmd for part in ("cd ", "cd\t", "cd\n", "pushd", "popd")) or cmd.strip() == "cd"
            exec_cmd = f"{cmd}\n__SHX_PWD__=$PWD\necho '__SHX_PWD__:'$__SHX_PWD__" if has_cd else cmd

            process = subprocess.run(
                exec_cmd,
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

            # Extract tracked directory if present
            if has_cd and exit_code == 0 and "__SHX_PWD__:" in stdout:
                parts = stdout.split("__SHX_PWD__:")
                stdout = parts[0]
                new_pwd = parts[-1].strip().splitlines()[0].strip()
                if os.path.isdir(new_pwd):
                    self.cwd = new_pwd

            combined = ""
            if stdout:
                combined += stdout
            if stderr:
                if combined:
                    combined += "\n--- STDERR ---\n"
                combined += stderr

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
                "command": cmd,
                "cwd": self.cwd,
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
