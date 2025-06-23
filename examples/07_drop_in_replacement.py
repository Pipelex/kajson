#!/usr/bin/env python3
"""
Drop-in Replacement Usage Example

This example demonstrates how Kajson can be used as a drop-in replacement
for Python's standard json module, handling complex types seamlessly.
"""

# Simply change your import
from datetime import datetime

import kajson as json  # Instead of: import json
from kajson import kajson, kajson_manager


def main():
    print("=== Drop-in Replacement Usage Example ===\n")

    print("Using kajson as a drop-in replacement for standard json...")

    # All your existing code works!
    data = {"user": "Alice", "logged_in": datetime.now()}
    print(f"Original data: {data}")
    print(f"Logged in type: {type(data['logged_in'])}")

    json_str = json.dumps(data)  # Works with datetime!
    print(f"\nSerialized JSON: {json_str}")

    restored = json.loads(json_str)
    print(f"\nRestored data: {restored}")
    print(f"Restored logged_in type: {type(restored['logged_in'])}")

    print("\n✅ Standard json module replaced seamlessly!")

    # Or use kajson directly
    import kajson

    print("\nAlternatively, using kajson directly:")
    json_str2 = kajson.dumps(data)
    restored2 = kajson.loads(json_str2)

    print(f"Direct kajson result: {restored2}")
    assert restored == restored2
    print("✅ Both approaches work identically!")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
