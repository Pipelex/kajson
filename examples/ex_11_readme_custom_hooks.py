#!/usr/bin/env python3
"""
README Custom Classes with Hooks Example

This example shows how to add JSON serialization support to custom classes
using the __json_encode__ and __json_decode__ hook methods.
"""

from typing import Any, Dict

from typing_extensions import override

import kajson
from kajson import kajson_manager


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __json_encode__(self):
        """Called by Kajson during serialization"""
        return {"x": self.x, "y": self.y}

    @classmethod
    def __json_decode__(cls, data: Dict[str, Any]):
        """Called by Kajson during deserialization"""
        return cls(data["x"], data["y"])

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return self.x == other.x and self.y == other.y

    @override
    def __repr__(self) -> str:
        return f"Vector(x={self.x}, y={self.y})"


def main():
    print("=== README Custom Classes with Hooks Example ===\n")

    # Works automatically!
    vector = Vector(3.14, 2.71)
    print(f"Original vector: {vector}")
    print(f"Vector type: {type(vector)}")

    json_str = kajson.dumps(vector)
    print(f"\nSerialized JSON: {json_str}")

    restored = kajson.loads(json_str)
    print(f"\nRestored vector: {restored}")
    print(f"Restored type: {type(restored)}")

    assert vector == restored
    print("✅ Vectors are equal - custom hooks work perfectly!")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
