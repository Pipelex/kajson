#!/usr/bin/env python3
"""
Generic Pydantic Models Example

This example demonstrates how Kajson seamlessly handles generic Pydantic models
with type parameters, preserving all type information during serialization and
deserialization. Perfect for type-safe containers, APIs, and data structures.
"""

from typing import Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel
from typing_extensions import override

from kajson import kajson, kajson_manager

# Define type variables for generic models
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Container(BaseModel, Generic[T]):
    """A generic container that can hold any type safely."""

    name: str
    items: List[T]
    capacity: int

    def add_item(self, item: T) -> None:
        """Add an item to the container."""
        if len(self.items) < self.capacity:
            self.items.append(item)

    def get_summary(self) -> str:
        return f"Container '{self.name}' with {len(self.items)}/{self.capacity} items"


class KeyValueStore(BaseModel, Generic[K, V]):
    """A generic key-value store with typed keys and values."""

    name: str
    data: Dict[K, V]
    created_by: str

    def get_keys(self) -> List[K]:
        return list(self.data.keys())

    def get_values(self) -> List[V]:
        return list(self.data.values())


class ApiResponse(BaseModel, Generic[T]):
    """A generic API response wrapper."""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: str

    def is_successful(self) -> bool:
        return self.success and self.data is not None


class User(BaseModel):
    """User model for API responses."""

    id: int
    name: str
    email: str


class Product(BaseModel):
    """Product model for API responses."""

    id: int
    name: str
    price: float
    category: str


# Bounded generic example
class Numeric(BaseModel):
    """Base class for numeric types."""

    def get_value(self) -> Union[int, float]:
        raise NotImplementedError


class IntegerValue(Numeric):
    """Integer implementation."""

    value: int

    @override
    def get_value(self) -> int:
        return self.value


class FloatValue(Numeric):
    """Float implementation."""

    value: float

    @override
    def get_value(self) -> float:
        return self.value


# Bounded type variable
NumericType = TypeVar("NumericType", bound=Numeric)


class Calculator(BaseModel, Generic[NumericType]):
    """A generic calculator that works with numeric types."""

    name: str
    operands: List[NumericType]

    def sum_values(self) -> Union[int, float]:
        return sum(operand.get_value() for operand in self.operands)


def main():
    print("=== Generic Pydantic Models Example ===\n")

    # 1. Simple generic container with different types
    print("1. Generic Containers with Type Parameters")
    print("-" * 40)

    # String container
    string_container = Container[str](name="fruits", items=["apple", "banana", "cherry"], capacity=10)

    # Integer container
    int_container = Container[int](name="numbers", items=[1, 2, 3, 4, 5], capacity=20)

    print(f"String container: {string_container.get_summary()}")
    print(f"Items: {string_container.items}")
    print(f"Int container: {int_container.get_summary()}")
    print(f"Items: {int_container.items}")

    # Serialize containers
    string_json = kajson.dumps(string_container, indent=2)
    int_json = kajson.dumps(int_container, indent=2)

    print(f"\nSerialized string container:\n{string_json}")

    # Deserialize and verify
    restored_string = kajson.loads(string_json)
    restored_int = kajson.loads(int_json)

    assert restored_string == string_container
    assert restored_int == int_container
    print("✅ Generic containers serialized and restored perfectly!")

    # 2. Multiple type parameters
    print("\n\n2. Multiple Type Parameters")
    print("-" * 40)

    # String -> Int mapping
    user_scores = KeyValueStore[str, int](name="user_scores", data={"alice": 95, "bob": 87, "charlie": 92}, created_by="admin")

    print(f"Store: {user_scores.name}")
    print(f"Keys: {user_scores.get_keys()}")
    print(f"Values: {user_scores.get_values()}")

    # Serialize and restore
    scores_json = kajson.dumps(user_scores)
    restored_scores = kajson.loads(scores_json)

    assert restored_scores == user_scores
    print("✅ Multi-parameter generic model works perfectly!")

    # 3. Generic API responses
    print("\n\n3. Generic API Response Patterns")
    print("-" * 40)

    # User response
    user_response = ApiResponse[User](success=True, data=User(id=1, name="Alice", email="alice@example.com"), timestamp="2025-01-15T10:30:00Z")

    # Product list response
    product_response = ApiResponse[List[Product]](
        success=True,
        data=[Product(id=1, name="Widget", price=19.99, category="Tools"), Product(id=2, name="Gadget", price=29.99, category="Electronics")],
        timestamp="2025-01-15T10:35:00Z",
    )

    # Error response
    error_response = ApiResponse[str](success=False, error="User not found", timestamp="2025-01-15T10:40:00Z")

    print(f"User response successful: {user_response.is_successful()}")
    print(f"User data: {user_response.data}")
    print(f"Product response successful: {product_response.is_successful()}")
    print(f"Error response: {error_response.error}")

    # Serialize all responses
    user_json = kajson.dumps(user_response)
    product_json = kajson.dumps(product_response)
    error_json = kajson.dumps(error_response)

    # Restore all responses
    restored_user_resp = kajson.loads(user_json)
    restored_product_resp = kajson.loads(product_json)
    restored_error_resp = kajson.loads(error_json)

    # Verify types are preserved
    assert isinstance(restored_user_resp.data, User)
    assert isinstance(restored_product_resp.data, list)
    assert restored_error_resp.data is None

    print("✅ Generic API responses work perfectly with complex nested types!")

    # 4. Bounded generics
    print("\n\n4. Bounded Generic Types")
    print("-" * 40)

    # Integer calculator
    int_calc = Calculator[IntegerValue](name="integer_calculator", operands=[IntegerValue(value=10), IntegerValue(value=20), IntegerValue(value=30)])

    # Float calculator
    float_calc = Calculator[FloatValue](name="float_calculator", operands=[FloatValue(value=10.5), FloatValue(value=20.7), FloatValue(value=30.2)])

    print(f"Integer calculator sum: {int_calc.sum_values()}")
    print(f"Float calculator sum: {float_calc.sum_values()}")

    # Serialize calculators
    int_calc_json = kajson.dumps(int_calc)
    float_calc_json = kajson.dumps(float_calc)

    # Restore calculators
    restored_int_calc = kajson.loads(int_calc_json)
    restored_float_calc = kajson.loads(float_calc_json)

    # Verify bounded types work
    assert isinstance(restored_int_calc.operands[0], IntegerValue)
    assert isinstance(restored_float_calc.operands[0], FloatValue)
    assert restored_int_calc.sum_values() == 60
    assert abs(restored_float_calc.sum_values() - 61.4) < 0.01

    print("✅ Bounded generic types maintain type safety!")

    print("\n🎉 All generic model patterns work seamlessly with Kajson!")
    print("\nKey Features Demonstrated:")
    print("• Single type parameter containers: Container[T]")
    print("• Multiple type parameters: KeyValueStore[K, V]")
    print("• Nested generics: ApiResponse[List[Product]]")
    print("• Bounded generics: Calculator[NumericType]")
    print("• Perfect type preservation during serialization/deserialization")
    print("• No special handling required - it just works!")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
