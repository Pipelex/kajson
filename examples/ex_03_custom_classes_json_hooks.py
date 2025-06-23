#!/usr/bin/env python3
"""
Custom Classes with JSON Hooks Example

This example demonstrates how to add JSON serialization support to custom classes
using the __json_encode__ and __json_decode__ methods.
"""

from typing import Any, Dict

from typing_extensions import override

from kajson import kajson, kajson_manager


class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __json_encode__(self):
        """Called during serialization"""
        return {"x": self.x, "y": self.y}

    @classmethod
    def __json_decode__(cls, data: Dict[str, Any]):
        """Called during deserialization"""
        return cls(data["x"], data["y"])

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y

    @override
    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"


def main():
    print("=== Custom Classes with JSON Hooks Example ===\n")

    # Use it directly
    point = Point(3.14, 2.71)
    print(f"Original point: {point}")
    print(f"Point type: {type(point)}")

    json_str = kajson.dumps(point)
    print(f"\nSerialized JSON: {json_str}")

    restored = kajson.loads(json_str)
    print(f"\nRestored point: {restored}")
    print(f"Restored type: {type(restored)}")

    # Verify equality
    assert point == restored
    print("\n✅ Perfect reconstruction! Original and restored points are equal.")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
