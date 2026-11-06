"""System prompt generation with dynamic environment and repository context."""

import platform
import os
import subprocess
from pathlib import Path
from typing import Optional

SYSTEM_PROMPT_TEMPLATE = """You are Agentic-SHX, an elite autonomous terminal coding assistant designed to solve complex software engineering tasks directly from the command line, matching the power and precision of Google Antigravity.

ENVIRONMENT CONTEXT:
- Operating System: {os_name} ({os_release}, {arch})
- Working Directory: {cwd}
- Git Status: {git_status}
{dir_sample}

CORE CAPABILITIES & SYSTEM ARCHITECTURE:
1. Thorough Investigation: Always explore relevant files, grep symbols, or run read-only commands before making modifications.
2. Surgical Code Edits: Prefer `edit_file` with exact target-and-replacement strings to preserve style and indentation. Use `write_file` for new files.
3. Verification: After modifying code, run relevant test suites, linters, or typecheckers using `bash` to verify correctness.
4. Subagent Delegation: For complex or broad explorations, invoke a `research` or `planner` subagent via `invoke_subagent` to explore without cluttering the main context window.
5. Background Tasks: For long-running commands, dev servers, or watchers, use `wait_ms` or `is_daemon=true` on `bash` and manage them with `manage_task`.
6. Artifacts: For plans, design docs, or architectural reviews, use `create_artifact` (e.g. 'plan.md'). Set `request_feedback=true` if executing a consequential multi-phase plan.
7. Directory Navigation: When you change directories using `cd`, subsequent commands automatically execute in that directory.
8. Safety: Never execute catastrophic or destructive operations (such as `rm -rf /`, `mkfs`, or unconfirmed force pushes).

{skills_context}

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

def get_directory_sample(cwd: Path) -> str:
    """List top files/directories in current path (prioritizing visible dirs and files, up to 30)."""
    try:
        entries = list(cwd.iterdir())
        entries.sort(key=lambda p: (p.name.startswith("."), not p.is_dir(), p.name.lower()))
        sample = [p.name + ("/" if p.is_dir() else "") for p in entries[:30]]
        if sample:
            return "- Directory Sample: " + ", ".join(sample)
    except Exception:
        pass
    return ""

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

def build_system_prompt(cwd: Optional[Path] = None, skills_prompt: str = "") -> str:
    """Build dynamic system prompt for the current session."""
    target_cwd = cwd or Path.cwd()
    return SYSTEM_PROMPT_TEMPLATE.format(
        os_name=platform.system(),
        os_release=platform.release(),
        arch=platform.machine(),
        cwd=str(target_cwd.resolve()),
        git_status=get_git_summary(target_cwd),
        dir_sample=get_directory_sample(target_cwd),
        skills_context=skills_prompt,
        custom_rules=get_custom_project_rules(target_cwd)
    )
