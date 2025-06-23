#!/usr/bin/env python3
"""
Error Handling with Validation Example

This example shows how Kajson handles validation errors when deserializing
JSON data that doesn't meet Pydantic model constraints.
"""

from pydantic import BaseModel, Field

from kajson import kajson, kajson_manager


class Product(BaseModel):
    name: str
    price: float = Field(gt=0)  # Must be positive


def main():
    print("=== Error Handling with Validation Example ===\n")

    # Valid data works fine
    product = Product(name="Widget", price=19.99)
    print(f"Valid product: {product}")

    json_str = kajson.dumps(product)
    print(f"Serialized JSON: {json_str}")

    restored = kajson.loads(json_str)
    print(f"Restored product: {restored}")
    print("✅ Valid data works perfectly!\n")

    # Invalid data in JSON
    invalid_json = """
{
    "name": "Widget",
    "price": -10,
    "__class__": "Product",
    "__module__": "__main__"
}
"""

    print("Attempting to load invalid JSON with negative price...")
    print(f"Invalid JSON: {invalid_json.strip()}")

    try:
        kajson.loads(invalid_json)
        print("❌ This should not happen - validation should fail!")
    except kajson.KajsonDecoderError:
        print("✅ Validation failed as expected!")
        print("   Kajson properly caught the Pydantic validation error:")
        print("   → Price must be greater than 0 (got -10)")
        print("   This ensures data integrity when deserializing!")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
