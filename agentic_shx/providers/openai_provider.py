"""OpenAI, OpenRouter, and Ollama provider implementation via standard Chat Completions API."""

import json
import os
from typing import List, Dict, Any, Optional, Callable
import httpx
from agentic_shx.providers.base import BaseProvider, ProviderResponse, ToolCall

class OpenAIProvider(BaseProvider):
    """OpenAI-compatible provider supporting OpenAI, OpenRouter, Ollama, Groq, DeepSeek."""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        is_ollama = "ollama" in model.lower()
        clean_model = model.replace("openai/", "").replace("ollama/", "").replace("openrouter/", "")
        
        default_base_url = "http://localhost:11434/v1" if is_ollama else "https://api.openai.com/v1"
        if "openrouter" in model.lower():
            default_base_url = "https://openrouter.ai/api/v1"

        actual_base = base_url or os.getenv("OPENAI_BASE_URL") or default_base_url
        actual_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or ("ollama" if is_ollama else None)

        super().__init__(model=clean_model, api_key=actual_key, base_url=actual_base)
        if not self.api_key and not is_ollama:
            raise ValueError(
                f"API key not found for {model}. Please set OPENAI_API_KEY or OPENROUTER_API_KEY."
            )

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        on_thought_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResponse:
        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'ollama'}"
        }

        # Format tool calls in assistant messages to match OpenAI schema
        formatted_messages = []
        for m in messages:
            msg_copy = dict(m)
            if msg_copy.get("role") == "assistant" and "tool_calls" in msg_copy:
                tcs = []
                for tc in msg_copy["tool_calls"]:
                    if isinstance(tc, ToolCall):
                        tcs.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else tc.arguments
                            }
                        })
                    else:
                        tcs.append(tc)
                msg_copy["tool_calls"] = tcs
            formatted_messages.append(msg_copy)

        body: Dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True}
        }
        if tools:
            body["tools"] = tools

        full_content = []
        full_thinking = []
        tool_calls_dict: Dict[int, Dict[str, Any]] = {}
        p_tokens = 0
        c_tokens = 0

        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", endpoint, json=body, headers=headers) as resp:
                if resp.status_code != 200:
                    err_text = resp.read().decode("utf-8")
                    raise RuntimeError(f"OpenAI/Ollama API Error [{resp.status_code}]: {err_text}")

                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    # Usage check
                    if "usage" in chunk and chunk["usage"]:
                        p_tokens = chunk["usage"].get("prompt_tokens", p_tokens)
                        c_tokens = chunk["usage"].get("completion_tokens", c_tokens)

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})

                    # Text delta
                    if "content" in delta and delta["content"]:
                        content_piece = delta["content"]
                        full_content.append(content_piece)
                        if on_content_chunk:
                            on_content_chunk(content_piece)

                    # Reasoning / Thinking delta (e.g. DeepSeek-R1 / o1 / o3)
                    if "reasoning_content" in delta and delta["reasoning_content"]:
                        thought_piece = delta["reasoning_content"]
                        full_thinking.append(thought_piece)
                        if on_thought_chunk:
                            on_thought_chunk(thought_piece)

                    # Tool calls delta
                    if "tool_calls" in delta and delta["tool_calls"]:
                        for tc_chunk in delta["tool_calls"]:
                            idx = tc_chunk.get("index", 0)
                            if idx not in tool_calls_dict:
                                tool_calls_dict[idx] = {
                                    "id": tc_chunk.get("id", f"call_{idx}"),
                                    "name": "",
                                    "arguments": ""
                                }
                            if "id" in tc_chunk and tc_chunk["id"]:
                                tool_calls_dict[idx]["id"] = tc_chunk["id"]
                            fn = tc_chunk.get("function", {})
                            if "name" in fn and fn["name"]:
                                tool_calls_dict[idx]["name"] += fn["name"]
                            if "arguments" in fn and fn["arguments"]:
                                tool_calls_dict[idx]["arguments"] += fn["arguments"]

        # Parse assembled tool calls
        final_tool_calls: List[ToolCall] = []
        for idx in sorted(tool_calls_dict.keys()):
            tc = tool_calls_dict[idx]
            try:
                args = json.loads(tc["arguments"]) if tc["arguments"].strip() else {}
            except Exception:
                args = {"raw_args": tc["arguments"]}
            final_tool_calls.append(
                ToolCall(id=tc["id"], name=tc["name"], arguments=args)
            )

        return ProviderResponse(
            content="".join(full_content),
            thinking="".join(full_thinking),
            tool_calls=final_tool_calls,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens
        )
