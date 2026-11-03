"""File operations: read, write, and surgical search/replace editing."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from agentic_shx.tools.base import BaseTool, ToolResult

def _resolve_path(path_str: str, base_dir: str) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = Path(base_dir) / p
    return p.resolve()

def _is_binary_file(filepath: Path) -> bool:
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except Exception:
        return False


class ReadFileTool(BaseTool):
    """Reads file content with line numbers and optional line slicing."""

    name = "read_file"
    description = (
        "Read the contents of a text file. Each line is prefixed with its line number "
        "(e.g. '1: code'). You can specify start_line and end_line for large files."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path (relative to workspace or absolute)."
            },
            "start_line": {
                "type": "integer",
                "description": "Optional 1-based start line number to read from."
            },
            "end_line": {
                "type": "integer",
                "description": "Optional 1-based end line number to read to (inclusive)."
            }
        },
        "required": ["path"]
    }

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = cwd or os.getcwd()

    def execute(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, **kwargs) -> ToolResult:
        resolved = _resolve_path(path, self.cwd)
        if not resolved.exists():
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        if resolved.is_dir():
            return ToolResult(success=False, output="", error=f"Path is a directory, not a file: {path}")
        if _is_binary_file(resolved):
            return ToolResult(success=False, output="", error=f"Cannot read binary file: {path}")

        try:
            with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            s_idx = max(1, start_line) if start_line else 1
            e_idx = min(total_lines, end_line) if end_line else total_lines

            if s_idx > total_lines:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Start line {s_idx} is beyond total file lines ({total_lines})."
                )

            selected_lines = lines[s_idx - 1:e_idx]
            formatted_output = "".join(
                f"{s_idx + i:6d} | {line}" for i, line in enumerate(selected_lines)
            )

            header = f"=== File: {path} (Lines {s_idx}-{e_idx} of {total_lines}) ===\n"
            return ToolResult(success=True, output=header + formatted_output)

        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to read file: {str(e)}")


class WriteFileTool(BaseTool):
    """Creates or overwrites a file."""

    name = "write_file"
    description = (
        "Write full content to a file. Overwrites the file if it exists, "
        "or creates it (along with any missing parent directories) if it does not."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path (relative to workspace or absolute)."
            },
            "content": {
                "type": "string",
                "description": "The complete content to write into the file."
            }
        },
        "required": ["path", "content"]
    }

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = cwd or os.getcwd()

    def execute(self, path: str, content: str, **kwargs) -> ToolResult:
        resolved = _resolve_path(path, self.cwd)
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)
            byte_count = len(content.encode("utf-8"))
            return ToolResult(
                success=True,
                output=f"Successfully wrote {byte_count} bytes to {path}"
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to write file: {str(e)}")


class EditFileTool(BaseTool):
    """Performs surgical search-and-replace on a file."""

    name = "edit_file"
    description = (
        "Surgically edit a file by replacing an exact string match (target) "
        "with replacement text. target must match existing characters and whitespace exactly."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The file path."
            },
            "target": {
                "type": "string",
                "description": "Exact text block to replace."
            },
            "replacement": {
                "type": "string",
                "description": "New text to substitute in place of target."
            },
            "replace_all": {
                "type": "boolean",
                "description": "Whether to replace all occurrences if target matches multiple times. Default false."
            }
        },
        "required": ["path", "target", "replacement"]
    }

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = cwd or os.getcwd()

    def execute(self, path: str, target: str, replacement: str, replace_all: bool = False, **kwargs) -> ToolResult:
        resolved = _resolve_path(path, self.cwd)
        if not resolved.exists():
            return ToolResult(success=False, output="", error=f"File not found: {path}")

        try:
            with open(resolved, "r", encoding="utf-8") as f:
                content = f.read()

            occurrences = content.count(target)
            if occurrences == 0:
                return ToolResult(
                    success=False,
                    output="",
                    error=(
                        f"Target string not found in {path}. Make sure whitespace and "
                        f"indentation match exactly. Use read_file to check exact contents."
                    )
                )

            if occurrences > 1 and not replace_all:
                return ToolResult(
                    success=False,
                    output="",
                    error=(
                        f"Target string appears {occurrences} times in {path}. Please provide a larger "
                        f"unique surrounding context block, or set replace_all=true."
                    )
                )

            new_content = content.replace(target, replacement) if replace_all else content.replace(target, replacement, 1)

            with open(resolved, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult(
                success=True,
                output=f"Successfully updated {path} (replaced {occurrences if replace_all else 1} occurrence(s))."
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to edit file: {str(e)}")
