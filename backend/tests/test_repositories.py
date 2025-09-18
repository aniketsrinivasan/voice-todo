from __future__ import annotations

from uuid import UUID, uuid4

from backend.schemas import TodoCreate, TodoUpdate
from backend.src.repositories import CategoriesRepository, TodosRepository


def main() -> None:
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    todos = TodosRepository()
    cats = CategoriesRepository()

    # Create
    created = todos.create(user_id, TodoCreate(description="Buy milk", priority="high", categories=["groceries"]))
    print("created:", created.model_dump())

    # Attach categories via service-like call
    cats.ensure_many(user_id, ["groceries"])  # ensure exists

    # List
    listed = todos.list(user_id, {"q": "buy"})
    print("listed_count:", len(listed))

    # Update
    updated = todos.update(user_id, created.id, TodoUpdate(priority="low", categories=["errands"]))
    print("updated_priority:", updated.priority)

    # Get
    fetched = todos.get(user_id, created.id)
    print("fetched_id:", str(fetched.id))

    # Delete
    todos.delete(user_id, created.id)
    try:
        todos.get(user_id, created.id)
    except KeyError:
        print("deleted: true")


if __name__ == "__main__":
    main()

