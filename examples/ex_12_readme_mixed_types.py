#!/usr/bin/env python3
"""
README Working with Mixed Types Example

This example demonstrates how Kajson handles complex data structures
containing mixed types including Pydantic models, datetime objects, and plain Python types.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from pydantic import BaseModel

import kajson
from kajson import kajson_manager


class Task(BaseModel):
    name: str
    created_at: datetime
    duration: timedelta
    metadata: Dict[str, Any]


def main():
    print("=== README Working with Mixed Types Example ===\n")

    # Create mixed-type list
    tasks = [
        Task(
            name="Data processing", created_at=datetime.now(), duration=timedelta(hours=2, minutes=30), metadata={"priority": "high", "cpu_cores": 8}
        ),
        {"raw_data": "Some plain dict"},
        datetime.now(),
        ["plain", "list", "items"],
    ]

    print("Original mixed-type list:")
    for i, task in enumerate(tasks):
        print(f"  [{i}] {task} (type: {type(task).__name__})")

    # Kajson handles everything!
    json_str = kajson.dumps(tasks)
    print(f"\nSerialized JSON (truncated): {json_str[:300]}...")

    restored_tasks = kajson.loads(json_str)

    print("\nRestored mixed-type list:")
    for i, task in enumerate(restored_tasks):
        print(f"  [{i}] {task} (type: {type(task).__name__})")

    # Type checking shows proper reconstruction
    assert isinstance(restored_tasks[0], Task)
    assert isinstance(restored_tasks[0].duration, timedelta)
    assert isinstance(restored_tasks[2], datetime)

    print("\n✅ All types perfectly preserved!")
    print(f"✅ Task duration: {restored_tasks[0].duration}")
    print(f"✅ Task metadata: {restored_tasks[0].metadata}")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
