#!/usr/bin/env python3
"""
Working with Lists of Mixed Types Example

This example demonstrates how Kajson handles lists containing different types
including Pydantic models, datetime objects, and plain Python structures.
"""

from datetime import date, datetime, time

from pydantic import BaseModel

from kajson import kajson, kajson_manager


class Task(BaseModel):
    name: str
    due_date: date


def main():
    print("=== Working with Lists of Mixed Types Example ===\n")

    # Mix different types in one list
    mixed_data = [
        Task(name="Review PR", due_date=date.today()),
        datetime.now(),
        {"plain": "dict"},
        ["plain", "list"],
        time(14, 30),
    ]

    print("Original mixed data:")
    for i, item in enumerate(mixed_data):
        print(f"  [{i}] {item} (type: {type(item).__name__})")

    # Kajson handles everything
    json_str = kajson.dumps(mixed_data)
    print(f"\nSerialized JSON (truncated): {json_str[:200]}...")

    restored = kajson.loads(json_str)

    print("\nRestored mixed data:")
    for i, item in enumerate(restored):
        print(f"  [{i}] {item} (type: {type(item).__name__})")

    # Types are preserved
    assert isinstance(restored[0], Task)
    assert isinstance(restored[1], datetime)
    assert isinstance(restored[4], time)

    print("\n✅ All types preserved correctly!")
    print(f"✅ Task object: {restored[0].name} due on {restored[0].due_date}")
    print(f"✅ Datetime object: {restored[1]}")
    print(f"✅ Time object: {restored[4]}")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
