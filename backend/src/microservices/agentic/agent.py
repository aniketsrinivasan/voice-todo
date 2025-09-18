from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from backend.schemas import AgentQuery, AgentResult
from backend.src.microservices.agentic.llm import LLMClient, OpenAILLMClient
from backend.src.services import TodosService


@dataclass
class AgentConfig:
    model: str = "gpt-4o-mini"
    api_key: str = "sk-dummy"


class AgentService:
    """Simple agent that routes based on mode and delegates to services.

    In the future this would register MCP tools and perform tool-calls. For now,
    it uses heuristics and direct service calls so the API is usable without external APIs.
    """

    def __init__(self, todos_service: TodosService, llm: Optional[LLMClient] = None, config: Optional[AgentConfig] = None) -> None:
        self._todos_service = todos_service
        self._llm = llm or OpenAILLMClient(api_key=(config.api_key if config else None))
        self._config = config or AgentConfig()

    def execute(self, user_id, query: AgentQuery) -> AgentResult:
        mode = query.mode
        prompt = (query.prompt or "").strip()

        if mode == "query":
            todos = self._todos_service.list(user_id, {"q": prompt})
            msg = f"Found {len(todos)} to-dos."
            return AgentResult(message=msg, data={"todos": [t.model_dump() for t in todos]})
        elif mode == "create":
            # Very naive extraction: use prompt as description
            created = self._todos_service.create(user_id, payload={"description": prompt, "priority": "med"})  # type: ignore[arg-type]
            return AgentResult(message=f"Created to-do: {created.description}", changes=[{"action": "create_todo", "id": str(created.id)}])
        else:
            # For edit/delete stubs, just echo
            resp = self._llm.generate(messages=[{"role": "user", "content": prompt}])
            msg = resp["choices"][0]["message"]["content"]
            return AgentResult(message=msg)


__all__ = ["AgentService", "AgentConfig"]
