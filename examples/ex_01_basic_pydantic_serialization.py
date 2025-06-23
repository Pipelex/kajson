#!/usr/bin/env python3
"""
Basic Pydantic Model Serialization Example

This example demonstrates how Kajson seamlessly handles Pydantic models
with datetime fields, providing perfect reconstruction of objects.
"""

from datetime import datetime

from pydantic import BaseModel

from kajson import kajson, kajson_manager


class User(BaseModel):
    name: str
    email: str
    created_at: datetime


def main():
    print("=== Basic Pydantic Model Serialization Example ===\n")

    # Create and serialize
    user = User(name="Alice", email="alice@example.com", created_at=datetime.now())

    print(f"Original user: {user}")
    print(f"User type: {type(user)}")
    print(f"Created at type: {type(user.created_at)}")

    # Serialize to JSON
    json_str = kajson.dumps(user, indent=2)
    print(f"\nSerialized JSON:\n{json_str}")

    # Deserialize back
    restored_user = kajson.loads(json_str)
    print(f"\nRestored user: {restored_user}")
    print(f"Restored type: {type(restored_user)}")
    print(f"Restored created_at type: {type(restored_user.created_at)}")

    # Verify perfect reconstruction
    assert user == restored_user  # ✅ Perfect reconstruction!
    print("\n✅ Perfect reconstruction! Original and restored users are equal.")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
