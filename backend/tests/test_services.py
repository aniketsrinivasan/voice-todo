from __future__ import annotations

from uuid import UUID

from backend.schemas import TodoCreate, TodoUpdate
from backend.src.repositories import CategoriesRepository, TodosRepository
from backend.src.services import TodosService


def main() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    todos_repo = TodosRepository()
    cats_repo = CategoriesRepository()
    service = TodosService(todos_repo, cats_repo)

    created = service.create(user_id, TodoCreate(description="Laundry", priority="med", categories=["home"]))
    print("created:", created.model_dump())

    this_week = service.list(user_id, {"window": "this_week"})
    print("this_week_count:", len(this_week))

    updated = service.update(user_id, created.id, TodoUpdate(description="Laundry today", priority="high"))
    print("updated_desc:", updated.description)

    fetched = service.get(user_id, created.id)
    print("fetched:", fetched.model_dump())

    service.delete(user_id, created.id)
    try:
        service.get(user_id, created.id)
    except KeyError:
        print("deleted: true")


if __name__ == "__main__":
    main()

