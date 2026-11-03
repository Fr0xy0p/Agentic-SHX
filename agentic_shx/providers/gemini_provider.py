"""Google Gemini provider implementation via REST streaming API."""

import json
import os
from typing import List, Dict, Any, Optional, Callable
import httpx
from agentic_shx.providers.base import BaseProvider, ProviderResponse, ToolCall

class GeminiProvider(BaseProvider):
    """Google Gemini provider supporting 2.5 Flash, 2.5 Pro, and 1.5 Pro with streaming tool use."""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        clean_model = model.replace("gemini/", "").replace("google/", "")
        super().__init__(model=clean_model, api_key=api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"), base_url=base_url)
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable, "
                "or configure it in ~/.agentic_shx/config.yaml"
            )

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert standard OpenAI-style tool declarations to Gemini format."""
        gemini_funcs = []
        for t in tools:
            if t.get("type") == "function":
                f = t.get("function", {})
                params = f.get("parameters", {})
                # Gemini doesn't like empty properties without type
                gemini_funcs.append({
                    "name": f.get("name"),
                    "description": f.get("description", ""),
                    "parameters": params if params.get("properties") else {"type": "OBJECT"}
                })
        return [{"functionDeclarations": gemini_funcs}] if gemini_funcs else []

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Convert unified chat messages to Gemini's system_instruction and contents."""
        system_instruction = None
        contents = []

        for m in messages:
            role = m.get("role")
            content = m.get("content", "")

            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                parts = []
                if content:
                    parts.append({"text": content})
                # Check for tool calls made by assistant
                for tc in m.get("tool_calls", []):
                    parts.append({
                        "functionCall": {
                            "name": tc["name"] if isinstance(tc, dict) else tc.name,
                            "args": tc["arguments"] if isinstance(tc, dict) else tc.arguments,
                        }
                    })
                if parts:
                    contents.append({"role": "model", "parts": parts})
            elif role == "tool":
                # Gemini functionResponse
                name = m.get("name", "tool_result")
                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": name,
                            "response": {"output": content}
                        }
                    }]
                })

        return system_instruction, contents

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        on_content_chunk: Optional[Callable[[str], None]] = None,
        on_thought_chunk: Optional[Callable[[str], None]] = None,
    ) -> ProviderResponse:
        system_instruction, contents = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools)

        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        if system_instruction:
            body["systemInstruction"] = system_instruction
        if gemini_tools:
            body["tools"] = gemini_tools

        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        )

        full_content = []
        full_thinking = []
        tool_calls: List[ToolCall] = []
        p_tokens = 0
        c_tokens = 0

        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", endpoint, json=body, headers={"Content-Type": "application/json"}) as resp:
                if resp.status_code != 200:
                    err_text = resp.read().decode("utf-8")
                    raise RuntimeError(f"Gemini API Error [{resp.status_code}]: {err_text}")

                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    # Extract usage metadata
                    usage = chunk_json.get("usageMetadata", {})
                    p_tokens = usage.get("promptTokenCount", p_tokens)
                    c_tokens = usage.get("candidatesTokenCount", c_tokens)

                    candidates = chunk_json.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])

                    for part in parts:
                        # Standard text chunk
                        if "text" in part:
                            txt = part["text"]
                            full_content.append(txt)
                            if on_content_chunk:
                                on_content_chunk(txt)

                        # Function / tool call
                        if "functionCall" in part:
                            fc = part["functionCall"]
                            call_id = f"call_{len(tool_calls) + 1}"
                            tool_calls.append(
                                ToolCall(
                                    id=call_id,
                                    name=fc.get("name", ""),
                                    arguments=fc.get("args", {})
                                )
                            )

        return ProviderResponse(
            content="".join(full_content),
            thinking="".join(full_thinking),
            tool_calls=tool_calls,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens
        )

