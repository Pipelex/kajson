#!/usr/bin/env python3
"""
README Basic Usage Example - Why Kajson?

This example demonstrates the problem with standard JSON and how Kajson solves it.
This is the main example from the README.md showing why Kajson is needed.
"""

import json
from datetime import datetime

from pydantic import BaseModel

from kajson import kajson, kajson_manager


class User(BaseModel):
    name: str
    created_at: datetime


def main():
    print("=== README Basic Usage Example - Why Kajson? ===\n")

    user = User(name="Alice", created_at=datetime.now())
    print(f"User object: {user}")
    print(f"User type: {type(user)}")

    # ❌ Standard json fails
    print("\n--- Trying with standard json module ---")
    try:
        json_str = json.dumps(user)
        print(f"Standard json result: {json_str}")
    except TypeError as e:
        print(f"❌ Standard json fails: {e}")

    # ✅ Just works!
    print("\n--- Trying with kajson ---")
    json_str = kajson.dumps(user)
    print(f"✅ Kajson works: {json_str}")

    restored_user = kajson.loads(json_str)
    print(f"Restored user: {restored_user}")
    print(f"Restored type: {type(restored_user)}")

    assert user == restored_user  # Perfect reconstruction!
    print("✅ Perfect reconstruction!")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
