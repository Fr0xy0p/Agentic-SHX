"""System prompt generation with dynamic environment and repository context."""

import platform
import os
import subprocess
from pathlib import Path
from typing import Optional

SYSTEM_PROMPT_TEMPLATE = """You are Agentic-SHX, an elite autonomous terminal coding assistant designed to solve complex software engineering tasks directly from the command line.

ENVIRONMENT CONTEXT:
- Operating System: {os_name} ({os_release}, {arch})
- Working Directory: {cwd}
- Git Status: {git_status}

CORE BEHAVIOR AND RULES:
1. Thoroughly Investigate First: Inspect files, search codebase, or run read-only commands to understand the structure before modifying code.
2. Surgical Modifications: When changing code, prefer `edit_file` with precise search-and-replace, or `write_file` for new files. Always preserve existing code comments and style.
3. Verify Your Work: After modifying files, run relevant build, lint, or test commands using `bash` to verify that your changes compile and pass tests.
4. Terminal Awareness: Output should be concise, professional, and directly answer the user's intent. Do not give boilerplate instructions when you can execute them directly.
5. Safety: Never run destructive commands (like `rm -rf /`, `mkfs`, raw drive writes, or unprompted force pushes).

{custom_rules}
"""

def get_git_summary(cwd: Path) -> str:
    """Extract current git branch and dirty status."""
    try:
        res = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")
            branch_info = lines[0] if lines else "unknown"
            dirty_count = len(lines) - 1 if len(lines) > 1 else 0
            return f"{branch_info} ({dirty_count} changed files)"
        return "Not a git repository"
    except Exception:
        return "Git not available"

def get_custom_project_rules(cwd: Path) -> str:
    """Load local project rules from .shxrules or AGENTIC.md if present."""
    for rule_file in [".shxrules", "AGENTIC.md", ".agentrules"]:
        rule_path = cwd / rule_file
        if rule_path.exists():
            try:
                content = rule_path.read_text(encoding="utf-8").strip()
                return f"\nPROJECT-SPECIFIC INSTRUCTIONS ({rule_file}):\n{content}\n"
            except Exception:
                pass
    return ""

def build_system_prompt(cwd: Optional[Path] = None) -> str:
    """Build dynamic system prompt for the current session."""
    target_cwd = cwd or Path.cwd()
    return SYSTEM_PROMPT_TEMPLATE.format(
        os_name=platform.system(),
        os_release=platform.release(),
        arch=platform.machine(),
        cwd=str(target_cwd.resolve()),
        git_status=get_git_summary(target_cwd),
        custom_rules=get_custom_project_rules(target_cwd)
    )
