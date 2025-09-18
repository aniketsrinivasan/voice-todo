from __future__ import annotations

from uuid import UUID

from backend.schemas import AgentQuery
from backend.src.microservices.agentic.agent import AgentService
from backend.src.repositories import CategoriesRepository, TodosRepository
from backend.src.services import TodosService


def main() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    todos_repo = TodosRepository()
    cats_repo = CategoriesRepository()
    todos_service = TodosService(todos_repo, cats_repo)
    agent = AgentService(todos_service)

    result_query = agent.execute(user_id, AgentQuery(prompt="laundry", mode="query"))
    print("query_message:", result_query.message)

    result_create = agent.execute(user_id, AgentQuery(prompt="Buy bread", mode="create"))
    print("create_message:", result_create.message)


if __name__ == "__main__":
    main()

