"""Permission and approval management."""

from enum import Enum
from typing import Set, Tuple
from agentic_shx.safety.analyzer import CommandAnalyzer, RiskLevel

class ApprovalChoice(str, Enum):
    YES = "yes"                 # Approve this execution
    ALWAYS = "always"           # Always approve this command prefix for this session
    NO = "no"                   # Deny this execution
    ABORT = "abort"             # Abort entire agent plan

class PermissionManager:
    """Tracks session permissions and decides whether to prompt the user."""

    def __init__(self, auto_approve_safe: bool = True):
        self.auto_approve_safe = auto_approve_safe
        self.session_allowed_prefixes: Set[str] = set()
        self.session_allowed_tools: Set[str] = set()

    def should_ask_permission(self, tool_name: str, arguments: dict) -> Tuple[bool, RiskLevel, str]:
        """
        Determines if a tool call needs user approval.
        Returns: (needs_approval, risk_level, reason)
        """
        if tool_name in self.session_allowed_tools:
            return False, RiskLevel.SAFE, "Tool allowed for this session"

        if tool_name == "bash":
            command = arguments.get("command", "").strip()
            risk, reason = CommandAnalyzer.analyze(command)

            if risk == RiskLevel.CRITICAL_BLOCKED:
                return True, risk, reason

            # Check if this command matches any previously session-approved prefix
            for prefix in self.session_allowed_prefixes:
                if command.startswith(prefix):
                    return False, RiskLevel.SAFE, f"Matched session allowed prefix '{prefix}'"

            # Auto-approve safe read-only commands if configured
            if self.auto_approve_safe and risk == RiskLevel.SAFE:
                return False, risk, reason

            return True, risk, reason

        elif tool_name in ("write_file", "edit_file"):
            # File modifications are moderate risk
            path = arguments.get("path", "")
            return False, RiskLevel.MODERATE, f"Modifying file: {path}"

        elif tool_name in ("read_file", "search_files", "list_files", "git_status", "git_diff"):
            # Safe read-only inspection tools
            return False, RiskLevel.SAFE, "Read-only inspection tool"

        # Default fallback
        return True, RiskLevel.MODERATE, f"Tool execution: {tool_name}"

    def record_session_allow(self, tool_name: str, arguments: dict) -> None:
        """Remember approval for this session."""
        if tool_name == "bash":
            command = arguments.get("command", "").strip()
            # Extract first token or binary name (e.g., 'pytest', 'git status', 'cargo check')
            tokens = command.split()
            if tokens:
                prefix = tokens[0]
                if len(tokens) > 1 and tokens[0] in ("git", "npm", "cargo", "docker", "python", "python3"):
                    prefix = f"{tokens[0]} {tokens[1]}"
                self.session_allowed_prefixes.add(prefix)
        else:
            self.session_allowed_tools.add(tool_name)
