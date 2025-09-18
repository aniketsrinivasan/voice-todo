from __future__ import annotations

from datetime import datetime, timezone

from backend.schemas import TodoCreate, TodoOut, TodoUpdate


def main() -> None:
    create = TodoCreate(description="Test todo", priority="med")
    print("create_priority:", create.priority)

    now = datetime.now(timezone.utc)
    out = TodoOut(
        id=create.model_fields.get("id", None) or __import__("uuid").uuid4(),
        user_id=__import__("uuid").uuid4(),
        description=create.description,
        priority=create.priority,
        due_at=None,
        created_at=now,
        updated_at=now,
        metadata=None,
        categories=["x"],
        transcription_id=None,
    )
    print("out_description:", out.description)

    upd = TodoUpdate(description="Updated")
    print("update_has_description:", upd.description is not None)


if __name__ == "__main__":
    main()

