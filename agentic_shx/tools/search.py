"""Codebase search and directory exploration tools."""

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from agentic_shx.tools.base import BaseTool, ToolResult

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".idea", ".vscode", "dist", "build", ".egg-info"
}

class SearchFilesTool(BaseTool):
    """Searches file contents using regular expressions."""

    name = "search_files"
    description = (
        "Search for a regex or text pattern across files in the workspace. "
        "Respects common ignore directories (.git, node_modules, .venv, etc.)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Regex pattern or keyword to search for."
            },
            "path": {
                "type": "string",
                "description": "Optional subdirectory or file to search within. Defaults to project root."
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of matching lines to return. Defaults to 50."
            }
        },
        "required": ["query"]
    }

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = Path(cwd or os.getcwd()).resolve()

    def execute(self, query: str, path: Optional[str] = None, max_results: int = 50, **kwargs) -> ToolResult:
        search_root = (self.cwd / path).resolve() if path else self.cwd
        if not search_root.exists():
            return ToolResult(success=False, output="", error=f"Path not found: {path}")

        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error as e:
            return ToolResult(success=False, output="", error=f"Invalid regex query: {e}")

        matches = []
        try:
            if search_root.is_file():
                files_to_check = [search_root]
            else:
                files_to_check = []
                for root, dirs, files in os.walk(search_root):
                    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
                    for file in files:
                        files_to_check.append(Path(root) / file)

            for file_path in files_to_check:
                if len(matches) >= max_results:
                    break
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, start=1):
                            if pattern.search(line):
                                rel_path = file_path.relative_to(self.cwd)
                                matches.append(f"{rel_path}:{line_num}: {line.strip()}")
                                if len(matches) >= max_results:
                                    break
                except Exception:
                    continue

            if not matches:
                return ToolResult(success=True, output=f"No matches found for query: '{query}'")

            header = f"Found {len(matches)} match(es) for '{query}':\n"
            return ToolResult(success=True, output=header + "\n".join(matches))

        except Exception as e:
            return ToolResult(success=False, output="", error=f"Search failed: {str(e)}")


class ListFilesTool(BaseTool):
    """Lists files and directories matching a glob pattern."""

    name = "list_files"
    description = (
        "List files and directories in the project. Supports glob patterns (e.g. '**/*.py', 'src/*')."
    )
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match files against (default '*')."
            },
            "path": {
                "type": "string",
                "description": "Directory to list. Defaults to workspace root."
            },
            "max_results": {
                "type": "integer",
                "description": "Max entries to return (default 100)."
            }
        }
    }

    def __init__(self, cwd: Optional[str] = None):
        self.cwd = Path(cwd or os.getcwd()).resolve()

    def execute(self, pattern: str = "*", path: Optional[str] = None, max_results: int = 100, **kwargs) -> ToolResult:
        base = (self.cwd / path).resolve() if path else self.cwd
        if not base.exists():
            return ToolResult(success=False, output="", error=f"Path not found: {path}")

        results = []
        try:
            for item in base.glob(pattern):
                # Filter excluded directories
                if any(excluded in item.parts for excluded in EXCLUDED_DIRS):
                    continue
                rel_path = item.relative_to(self.cwd)
                prefix = "[DIR]  " if item.is_dir() else "[FILE] "
                results.append(f"{prefix}{rel_path}")
                if len(results) >= max_results:
                    break

            if not results:
                return ToolResult(success=True, output="No matching files found.")

            return ToolResult(success=True, output="\n".join(results))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to list files: {str(e)}")
