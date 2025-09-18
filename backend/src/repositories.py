from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID, uuid4

from backend.schemas import (
    CategoryOut,
    TodoCreate,
    TodoOut,
    TodoUpdate,
    TranscriptOut,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _TodoRecord:
    id: UUID
    user_id: UUID
    description: str
    priority: str
    due_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    transcription_id: Optional[UUID] = None


class TodosRepository:
    """In-memory repository for todos.

    This is a stand-in for a Supabase DAL, exposing a compatible API.
    """

    def __init__(self) -> None:
        self._todos: dict[UUID, _TodoRecord] = {}
        self._todo_to_categories: dict[UUID, set[str]] = {}

    def create(self, user_id: UUID, payload: TodoCreate) -> TodoOut:
        todo_id = uuid4()
        now = _utcnow()
        record = _TodoRecord(
            id=todo_id,
            user_id=user_id,
            description=payload.description,
            priority=payload.priority,
            due_at=payload.due_at,
            created_at=now,
            updated_at=now,
            metadata=payload.metadata or {},
        )
        self._todos[todo_id] = record
        if payload.categories:
            self._todo_to_categories[todo_id] = set(payload.categories)
        return self._to_out(record, categories=list(self._todo_to_categories.get(todo_id, set())))

    def get(self, user_id: UUID, todo_id: UUID) -> TodoOut:
        record = self._todos.get(todo_id)
        if record is None or record.user_id != user_id:
            raise KeyError("todo_not_found")
        return self._to_out(record, categories=list(self._todo_to_categories.get(todo_id, set())))

    def list(self, user_id: UUID, filters: Optional[dict[str, Any]] = None) -> List[TodoOut]:
        filters = filters or {}
        results: list[TodoOut] = []
        q = (filters.get("q") or "").lower()
        priority: Optional[str] = filters.get("priority")
        category: Optional[str] = filters.get("category")
        due_before: Optional[datetime] = filters.get("due_before")
        due_after: Optional[datetime] = filters.get("due_after")

        for record in self._todos.values():
            if record.user_id != user_id:
                continue
            if q and q not in record.description.lower():
                continue
            if priority and record.priority != priority:
                continue
            if due_before and (record.due_at is None or record.due_at >= due_before):
                continue
            if due_after and (record.due_at is None or record.due_at <= due_after):
                continue
            categories = self._todo_to_categories.get(record.id, set())
            if category and category not in categories:
                continue
            results.append(self._to_out(record, categories=list(categories)))
        # Simple sort by created_at desc for determinism
        results.sort(key=lambda t: t.created_at, reverse=True)
        return results

    def update(self, user_id: UUID, todo_id: UUID, payload: TodoUpdate) -> TodoOut:
        record = self._todos.get(todo_id)
        if record is None or record.user_id != user_id:
            raise KeyError("todo_not_found")
        if payload.description is not None:
            record.description = payload.description
        if payload.priority is not None:
            record.priority = payload.priority
        if payload.due_at is not None:
            record.due_at = payload.due_at
        if payload.metadata is not None:
            record.metadata = payload.metadata
        record.updated_at = _utcnow()
        if payload.categories is not None:
            self._todo_to_categories[record.id] = set(payload.categories)
        return self._to_out(record, categories=list(self._todo_to_categories.get(record.id, set())))

    def delete(self, user_id: UUID, todo_id: UUID) -> None:
        record = self._todos.get(todo_id)
        if record is None or record.user_id != user_id:
            raise KeyError("todo_not_found")
        self._todos.pop(todo_id, None)
        self._todo_to_categories.pop(todo_id, None)

    def attach_categories(self, user_id: UUID, todo_id: UUID, category_names: List[str]) -> None:
        record = self._todos.get(todo_id)
        if record is None or record.user_id != user_id:
            raise KeyError("todo_not_found")
        existing = self._todo_to_categories.get(todo_id, set())
        existing.update(category_names)
        self._todo_to_categories[todo_id] = existing

    @staticmethod
    def _to_out(record: _TodoRecord, categories: Optional[List[str]] = None) -> TodoOut:
        return TodoOut(
            id=record.id,
            user_id=record.user_id,
            description=record.description,
            priority=record.priority,  # type: ignore[arg-type]
            due_at=record.due_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
            metadata=record.metadata,
            categories=categories or [],
            transcription_id=record.transcription_id,
        )


class CategoriesRepository:
    """In-memory repository for categories."""

    def __init__(self) -> None:
        self._categories_by_user: dict[UUID, dict[str, CategoryOut]] = {}

    def ensure_many(self, user_id: UUID, names: List[str]) -> List[CategoryOut]:
        user_cats = self._categories_by_user.setdefault(user_id, {})
        out: list[CategoryOut] = []
        for name in names:
            if name not in user_cats:
                user_cats[name] = CategoryOut(id=uuid4(), name=name, created_at=_utcnow())
            out.append(user_cats[name])
        return out

    def list(self, user_id: UUID) -> List[CategoryOut]:
        return list(self._categories_by_user.get(user_id, {}).values())


class TranscriptsRepository:
    """In-memory repository for voice transcription records."""

    def __init__(self) -> None:
        self._transcripts: dict[UUID, TranscriptOut] = {}

    def create_pending(self, user_id: UUID, audio_uri: str, language: Optional[str]) -> TranscriptOut:
        rec = TranscriptOut(
            id=uuid4(),
            status="pending",
            text=None,
            error=None,
            created_at=_utcnow(),
        )
        self._transcripts[rec.id] = rec
        return rec

    def mark_done(self, id: UUID, text: str, metadata: Optional[dict[str, Any]] = None) -> TranscriptOut:
        rec = self._transcripts[id]
        self._transcripts[id] = rec.copy(update={"status": "done", "text": text})
        return self._transcripts[id]

    def mark_failed(self, id: UUID, error: str) -> TranscriptOut:
        rec = self._transcripts[id]
        self._transcripts[id] = rec.copy(update={"status": "failed", "error": error})
        return self._transcripts[id]

    def get(self, id: UUID) -> TranscriptOut:
        return self._transcripts[id]


class AuditRepository:
    """In-memory repository for audit logs."""

    def __init__(self) -> None:
        self._logs: list[dict[str, Any]] = []

    def record(self, user_id: UUID, action: str, payload: dict[str, Any]) -> None:
        self._logs.append({
            "id": str(uuid4()),
            "user_id": str(user_id),
            "action": action,
            "payload": payload,
            "created_at": _utcnow().isoformat(),
        })

    def list(self) -> Iterable[dict[str, Any]]:
        return list(self._logs)


__all__ = [
    "TodosRepository",
    "CategoriesRepository",
    "TranscriptsRepository",
    "AuditRepository",
]

