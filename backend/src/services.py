from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from backend.schemas import TodoCreate, TodoOut, TodoUpdate
from backend.src.repositories import CategoriesRepository, TodosRepository


class TodosService:
    """Business logic for managing to-do items.

    Validates inputs, orchestrates repository operations, and provides helpers
    for search windows like "due this week".
    """

    def __init__(self, todos_repo: TodosRepository, categories_repo: CategoriesRepository) -> None:
        self._todos_repo = todos_repo
        self._categories_repo = categories_repo

    def create(self, user_id: UUID, payload: TodoCreate) -> TodoOut:
        if payload.categories:
            self._categories_repo.ensure_many(user_id, payload.categories)
        return self._todos_repo.create(user_id, payload)

    def get(self, user_id: UUID, todo_id: UUID) -> TodoOut:
        return self._todos_repo.get(user_id, todo_id)

    def list(self, user_id: UUID, filters: Optional[dict[str, Any]] = None) -> List[TodoOut]:
        filters = dict(filters or {})
        # Expand shorthand date windows
        window = filters.pop("window", None)
        if window == "this_week":
            start, end = self._this_week_bounds()
            filters["due_after"] = start
            filters["due_before"] = end
        return self._todos_repo.list(user_id, filters)

    def update(self, user_id: UUID, todo_id: UUID, payload: TodoUpdate) -> TodoOut:
        if payload.categories:
            self._categories_repo.ensure_many(user_id, payload.categories)
        return self._todos_repo.update(user_id, todo_id, payload)

    def delete(self, user_id: UUID, todo_id: UUID) -> None:
        self._todos_repo.delete(user_id, todo_id)

    def attach_categories(self, user_id: UUID, todo_id: UUID, category_names: List[str]) -> None:
        if category_names:
            self._categories_repo.ensure_many(user_id, category_names)
        self._todos_repo.attach_categories(user_id, todo_id, category_names)

    @staticmethod
    def _this_week_bounds() -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        return start, end


__all__ = ["TodosService"]

