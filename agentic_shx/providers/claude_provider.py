"""Anthropic Claude provider implementation via Messages streaming API."""

import json
import os
from typing import List, Dict, Any, Optional, Callable
import httpx
from agentic_shx.providers.base import BaseProvider, ProviderResponse, ToolCall

class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider supporting Claude 3.7 Sonnet, 3.5 Sonnet, Haiku, Opus."""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        clean_model = model.replace("claude/", "").replace("anthropic/", "")
        super().__init__(
            model=clean_model,
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            base_url=base_url or "https://api.anthropic.com/v1"
        )
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable."
            )

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        claude_tools = []
        for t in tools:
            if t.get("type") == "function":
                f = t.get("function", {})
                claude_tools.append({
                    "name": f.get("name"),
                    "description": f.get("description", ""),
                    "input_schema": f.get("parameters", {"type": "object", "properties": {}})
                })
        return claude_tools

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        system_prompt = None
        converted = []

        for m in messages:
            role = m.get("role")
            content = m.get("content", "")

            if role == "system":
                system_prompt = content
            elif role == "user":
                converted.append({"role": "user", "content": content})
            elif role == "assistant":
                parts = []
                if content:
                    parts.append({"type": "text", "text": content})
                for tc in m.get("tool_calls", []):
                    tc_id = tc["id"] if isinstance(tc, dict) else tc.id
                    tc_name = tc["name"] if isinstance(tc, dict) else tc.name
                    tc_args = tc["arguments"] if isinstance(tc, dict) else tc.arguments
                    parts.append({
                        "type": "tool_use",
                        "id": tc_id,
                        "name": tc_name,
                        "input": tc_args
                    })
                converted.append({"role": "assistant", "content": parts or content})
            elif role == "tool":
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.get("tool_call_id", "call_1"),
                        "content": content
                    }]
                })

        return system_prompt, converted

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        on_thought_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResponse:
        endpoint = f"{self.base_url.rstrip('/')}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        system_prompt, formatted_messages = self._convert_messages(messages)
        claude_tools = self._convert_tools(tools)

        body: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if system_prompt:
            body["system"] = system_prompt
        if claude_tools:
            body["tools"] = claude_tools

        full_content = []
        tool_calls: List[ToolCall] = []
        current_tool_block = None
        p_tokens = 0
        c_tokens = 0

        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", endpoint, json=body, headers=headers) as resp:
                if resp.status_code != 200:
                    err_text = resp.read().decode("utf-8")
                    raise RuntimeError(f"Anthropic API Error [{resp.status_code}]: {err_text}")

                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type")

                    if event_type == "message_start":
                        msg = event.get("message", {})
                        usage = msg.get("usage", {})
                        p_tokens = usage.get("input_tokens", p_tokens)

                    elif event_type == "content_block_start":
                        cb = event.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            current_tool_block = {
                                "id": cb.get("id"),
                                "name": cb.get("name"),
                                "json_chunks": []
                            }

                    elif event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        delta_type = delta.get("type")

                        if delta_type == "text_delta":
                            txt = delta.get("text", "")
                            full_content.append(txt)
                            if on_content_chunk:
                                on_content_chunk(txt)

                        elif delta_type == "input_json_delta":
                            if current_tool_block:
                                current_tool_block["json_chunks"].append(delta.get("partial_json", ""))

                    elif event_type == "content_block_stop":
                        if current_tool_block:
                            json_str = "".join(current_tool_block["json_chunks"])
                            try:
                                args = json.loads(json_str) if json_str.strip() else {}
                            except Exception:
                                args = {"raw": json_str}
                            tool_calls.append(
                                ToolCall(
                                    id=current_tool_block["id"],
                                    name=current_tool_block["name"],
                                    arguments=args
                                )
                            )
                            current_tool_block = None

                    elif event_type == "message_delta":
                        usage = event.get("usage", {})
                        c_tokens = usage.get("output_tokens", c_tokens)

        return ProviderResponse(
            content="".join(full_content),
            tool_calls=tool_calls,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens
        )

