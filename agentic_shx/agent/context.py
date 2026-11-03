"""Conversation context and memory management."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from agentic_shx.providers.base import ToolCall

@dataclass
class ConversationContext:
    """Maintains message trajectory with compaction capabilities."""

    system_prompt: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    max_token_budget: int = 100_000

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str, tool_calls: Optional[List[ToolCall]] = None) -> None:
        msg: Dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)

    def add_tool_result(self, tool_call_id: str, tool_name: str, result_content: str) -> None:
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result_content
        })

    def get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """Combine system prompt and current messages for provider."""
        all_msgs = [{"role": "system", "content": self.system_prompt}]
        all_msgs.extend(self.messages)
        return all_msgs

    def estimate_tokens(self) -> int:
        """Rough token count estimation (~4 characters per token)."""
        total_chars = len(self.system_prompt)
        for m in self.messages:
            total_chars += len(str(m.get("content", "")))
            if "tool_calls" in m:
                total_chars += len(str(m["tool_calls"]))
        return total_chars // 4

    def compact_history(self) -> int:
        """
        Prunes large tool outputs from older turns in the conversation to save context.
        Returns the number of trimmed characters.
        """
        trimmed_chars = 0
        # Keep the latest 6 messages intact; compact older tool responses
        if len(self.messages) > 6:
            for m in self.messages[:-6]:
                if m.get("role") == "tool":
                    content = str(m.get("content", ""))
                    if len(content) > 500:
                        trimmed = len(content) - 300
                        trimmed_chars += trimmed
                        m["content"] = content[:150] + f"\n... [Output compacted ({trimmed} chars pruned)] ...\n" + content[-150:]
        return trimmed_chars

    def clear(self) -> None:
        self.messages.clear()

