from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from backend.schemas import TodoCreate, TodoOut, TodoUpdate
from backend.src.repositories import CategoriesRepository, TodosRepository
from backend.src.services import TodosService


app = FastAPI(title="Voice To-Do Backend", version="0.1.0")


def get_user_id() -> UUID:
    """Temporary auth dependency returning a static user id for now."""

    # Dummy user id; to be replaced by real auth later.
    return UUID("00000000-0000-0000-0000-000000000001")


# Initialize in-memory dependencies for now
_todos_repo = TodosRepository()
_categories_repo = CategoriesRepository()
_todos_service = TodosService(_todos_repo, _categories_repo)


@app.post("/todos", response_model=TodoOut)
def create_todo(payload: TodoCreate, user_id: UUID = Depends(get_user_id)) -> TodoOut:
    try:
        return _todos_service.create(user_id, payload)
    except ValueError as e:  # reserved for future validation
        raise HTTPException(status_code=400, detail={"code": "bad_request", "message": str(e)})


@app.get("/todos", response_model=list[TodoOut])
def list_todos(
    q: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    due_before: Optional[str] = Query(default=None),
    due_after: Optional[str] = Query(default=None),
    window: Optional[str] = Query(default=None),
    user_id: UUID = Depends(get_user_id),
) -> List[TodoOut]:
    filters: dict[str, Any] = {}
    if q:
        filters["q"] = q
    if priority:
        filters["priority"] = priority
    if category:
        filters["category"] = category
    if window:
        filters["window"] = window
    # For simplicity, due_before/after strings are ignored in this in-memory version
    return _todos_service.list(user_id, filters)


@app.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: UUID, user_id: UUID = Depends(get_user_id)) -> TodoOut:
    try:
        return _todos_service.get(user_id, todo_id)
    except KeyError:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Todo not found"})


@app.patch("/todos/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: UUID, payload: TodoUpdate, user_id: UUID = Depends(get_user_id)) -> TodoOut:
    try:
        return _todos_service.update(user_id, todo_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Todo not found"})


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: UUID, user_id: UUID = Depends(get_user_id)) -> dict[str, str]:
    try:
        _todos_service.delete(user_id, todo_id)
        return {"status": "ok"}
    except KeyError:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Todo not found"})


__all__ = ["app"]

