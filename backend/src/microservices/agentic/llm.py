from __future__ import annotations

from typing import Any, Optional


class LLMClient:
    """Protocol-like base for LLM clients used by the agent.

    Implementations should provide a `generate` method compatible with tool-calls.
    """

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


class OpenAILLMClient(LLMClient):
    """Minimal OpenAI client wrapper.

    Uses dummy key and model placeholders; to be overridden via environment in real deployments.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or "sk-dummy"
        self.model = model or "gpt-4o-mini"

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> dict[str, Any]:
        # For now, return an echo-style response for testing without external calls.
        last_user = next((m for m in reversed(messages) if m.get("role") == "user"), {"content": ""})
        return {
            "model": self.model,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": f"Echo: {last_user.get('content', '')}",
                    }
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }


__all__ = ["LLMClient", "OpenAILLMClient"]
