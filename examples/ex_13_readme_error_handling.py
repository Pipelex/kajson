#!/usr/bin/env python3
"""
README Error Handling Example

This example demonstrates how Kajson provides clear error messages
for validation issues when working with Pydantic models.
"""

from pydantic import BaseModel, Field

from kajson import kajson, kajson_manager


class Product(BaseModel):
    name: str
    price: float = Field(gt=0)  # Price must be positive


def main():
    print("=== README Error Handling Example ===\n")

    # First, show that valid data works
    valid_product = Product(name="Valid Widget", price=25.99)
    print(f"Valid product: {valid_product}")

    valid_json = kajson.dumps(valid_product)
    restored_valid = kajson.loads(valid_json)
    print(f"Valid product restored: {restored_valid}")
    print("✅ Valid data works perfectly!\n")

    # Invalid data
    json_str = '{"name": "Widget", "price": -10, "__class__": "Product", "__module__": "__main__"}'
    print(f"Attempting to load invalid JSON: {json_str}")

    try:
        product = kajson.loads(json_str)
        print(f"❌ This should not happen: {product}")
    except kajson.KajsonDecoderError:
        print("✅ Validation failed as expected!")
        print("   Kajson caught the Pydantic validation error:")
        print("   → Price must be greater than 0 (got -10)")
        print("   This prevents invalid data from being silently accepted!")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
