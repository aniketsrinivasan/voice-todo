from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TodoBase(BaseModel):
    """Shared fields for to-do items used across create/update/output.

    Attributes:
        description: A short description of the to-do item.
        priority: Priority level: low, med, or high.
        due_at: Optional due date/time for the to-do.
        categories: Optional list of category names to attach.
        metadata: Optional arbitrary metadata for internal use.
    """

    description: str = Field(..., min_length=1)
    priority: Literal["low", "med", "high"] = Field("med")
    due_at: Optional[datetime] = None
    categories: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class TodoCreate(TodoBase):
    """Payload to create a new to-do item."""

    pass


class TodoUpdate(BaseModel):
    """Payload to update an existing to-do item. All fields optional."""

    description: Optional[str] = None
    priority: Optional[Literal["low", "med", "high"]] = None
    due_at: Optional[datetime | None] = None
    categories: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class TodoOut(TodoBase):
    """Representation of a to-do item returned by the API."""

    id: UUID
    user_id: UUID
    transcription_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class CategoryCreate(BaseModel):
    """Payload to create a new category."""

    name: str = Field(..., min_length=1)


class CategoryOut(BaseModel):
    """Representation of a category returned by the API."""

    id: UUID
    name: str
    created_at: datetime


class TranscriptCreate(BaseModel):
    """Payload to submit a new audio transcription request."""

    audio_uri: str
    language: Optional[str] = None


class TranscriptOut(BaseModel):
    """Representation of a voice transcription record."""

    id: UUID
    status: Literal["pending", "done", "failed"]
    text: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime


class AgentQuery(BaseModel):
    """User request to the agent to perform an action."""

    prompt: str
    mode: Literal["query", "create", "edit", "delete"] = "query"
    context: Optional[dict[str, Any]] = None


class AgentResult(BaseModel):
    """Result returned by the agent containing message and optional structured data."""

    message: str
    changes: Optional[list[dict[str, Any]]] = None
    data: Optional[dict[str, Any]] = None


__all__ = [
    "TodoBase",
    "TodoCreate",
    "TodoUpdate",
    "TodoOut",
    "CategoryCreate",
    "CategoryOut",
    "TranscriptCreate",
    "TranscriptOut",
    "AgentQuery",
    "AgentResult",
]
