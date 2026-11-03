"""Command safety analysis and danger detection."""

import re
from enum import Enum
from typing import Tuple, List

class RiskLevel(str, Enum):
    SAFE = "SAFE"                 # Safe to auto-run (read-only, inspection)
    MODERATE = "MODERATE"         # Normal write/edit/build action (ask or auto depending on setting)
    DANGEROUS = "DANGEROUS"       # High risk (system modification, force delete, force push, sudo)
    CRITICAL_BLOCKED = "BLOCKED"  # Catastrophic actions (rm -rf /, disk wipe)


# Read-only or benign command prefixes that are generally safe to run without prompting
SAFE_COMMAND_PREFIXES = (
    "ls", "dir", "pwd", "whoami", "uname", "date", "echo", "printf",
    "cat", "head", "tail", "less", "more", "grep", "rg", "find", "wc",
    "file", "stat", "diff", "which", "where", "type",
    "git status", "git log", "git diff", "git show", "git branch", "git remote",
    "python --version", "python3 --version", "node -v", "npm -v", "cargo --version",
    "go version", "rustc --version", "docker ps", "docker images",
    "ps", "top -l 1", "uptime", "env", "printenv"
)

# Catastrophic command patterns that should be strictly blocked or require extreme explicit confirmation
BLOCKED_PATTERNS = [
    r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*\s+(/|~|\*)(\s|$)",  # rm -rf / or rm -rf ~ or rm -rf *
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",        # Fork bomb
    r"\bmkfs\b",                                         # Format disk
    r"\bdd\s+if=.*of=/dev/",                             # Overwriting raw block device
    r">\s*/dev/sd[a-z]",                                 # Writing to disk device
]

DANGEROUS_PATTERNS = [
    r"\bsudo\b",                                         # Privilege escalation
    r"\bdoas\b",
    r"\bsu\b",
    r"\bchmod\s+-R\s+777\b",
    r"\bchown\s+-R\b",
    r"\bgit\s+reset\s+--hard\b",                         # Destructive git reset
    r"\bgit\s+clean\s+-[a-zA-Z]*f",                      # Destructive git clean (e.g. -f, -fdx)
    r"\bgit\s+push\s+.*--force\b",                       # Force push
    r"\bcurl\b.*\|\s*(bash|sh|zsh)\b",                   # Piping web script to shell
    r"\bwget\b.*\|\s*(bash|sh|zsh)\b",
    r"\bkillall\b",
    r"\bshutdown\b",
    r"\breboot\b",
]


class CommandAnalyzer:
    """Analyzes shell commands for risk assessment."""

    @staticmethod
    def analyze(command: str) -> Tuple[RiskLevel, str]:
        cmd = command.strip()

        # Check for catastrophic blocked patterns
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return RiskLevel.CRITICAL_BLOCKED, f"Potentially catastrophic command blocked by safety rule: {pattern}"

        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return RiskLevel.DANGEROUS, f"High-risk command detected: {pattern}"

        # Check if it starts with a known safe read-only prefix
        # Split command by pipes or operators to ensure compound commands don't slip through
        subcommands = [s.strip() for s in re.split(r"&&|\|\||;|\|", cmd) if s.strip()]
        
        all_subcmds_safe = True
        for sub in subcommands:
            is_sub_safe = any(sub.startswith(prefix) for prefix in SAFE_COMMAND_PREFIXES)
            # Ensure no redirection to file (e.g., `echo "foo" > /etc/passwd`)
            if ">" in sub or ">>" in sub:
                is_sub_safe = False
            if not is_sub_safe:
                all_subcmds_safe = False
                break

        if all_subcmds_safe and subcommands:
            return RiskLevel.SAFE, "Read-only inspection command"

        return RiskLevel.MODERATE, "Standard execution / file modification command"
