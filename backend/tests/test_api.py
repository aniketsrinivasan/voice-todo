from __future__ import annotations

import json
from uuid import UUID

from fastapi.testclient import TestClient

from backend.src.api import app


def main() -> None:
    client = TestClient(app)

    # Create
    payload = {"description": "Call mom", "priority": "med", "categories": ["family"]}
    res = client.post("/todos", json=payload)
    print("status_post:", res.status_code)
    created = res.json()
    print("todo_id:", created["id"])

    # List
    res_list = client.get("/todos", params={"q": "call"})
    print("status_get_list:", res_list.status_code)
    print("list_count:", len(res_list.json()))

    # Get
    res_get = client.get(f"/todos/{created['id']}")
    print("status_get:", res_get.status_code)

    # Update
    res_patch = client.patch(f"/todos/{created['id']}", json={"priority": "high"})
    print("status_patch:", res_patch.status_code)
    print("new_priority:", res_patch.json()["priority"])

    # Delete
    res_del = client.delete(f"/todos/{created['id']}")
    print("status_delete:", res_del.status_code)

    # Confirm 404
    res_404 = client.get(f"/todos/{created['id']}")
    print("status_get_after_delete:", res_404.status_code)


if __name__ == "__main__":
    main()

