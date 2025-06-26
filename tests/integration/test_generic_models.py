# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for generic Pydantic models with type parameters.

These tests demonstrate Kajson's ability to handle generic models where:
- Models use TypeVar for parameterized types
- Generic models are instantiated with concrete types
- Serialization and deserialization preserve type information
"""

from __future__ import annotations

from typing import Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field
from typing_extensions import override

from kajson import kajson
from kajson.kajson_manager import KajsonManager

# Define type variables for generic models
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


# Define global classes for testing (so they can be imported normally)
class GlobalContainer(BaseModel, Generic[T]):
    """A generic container that can hold any type."""

    items: List[T]
    name: str
    count: int

    def get_summary(self) -> str:
        return f"Container '{self.name}' with {self.count} items"


class TestGenericModelsSerialization:
    """Tests demonstrating generic model serialization and deserialization."""

    def test_simple_generic_container_with_normal_import(self):
        """Test basic generic container with normal module import (not fake module)."""

        # Create instances with different concrete types
        string_container = GlobalContainer[str](items=["apple", "banana", "cherry"], name="fruit_basket", count=3)

        int_container = GlobalContainer[int](items=[1, 2, 3, 4, 5], name="numbers", count=5)

        print(f"String container: {string_container.get_summary()}")
        print(f"String items: {string_container.items}")
        print(f"Int container: {int_container.get_summary()}")
        print(f"Int items: {int_container.items}")

        # Serialize both containers
        string_json = kajson.dumps(string_container)
        int_json = kajson.dumps(int_container)

        print(f"\nString container JSON: {string_json}")
        print(f"Int container JSON: {int_json}")

        # Deserialize and verify (should work with normal imports)
        restored_string_container = kajson.loads(string_json)
        restored_int_container = kajson.loads(int_json)

        print(f"\nRestored string container: {restored_string_container.get_summary()}")
        print(f"Restored string items: {restored_string_container.items}")
        print(f"Restored int container: {restored_int_container.get_summary()}")
        print(f"Restored int items: {restored_int_container.items}")

        # Verify string container
        assert restored_string_container.name == "fruit_basket"
        assert restored_string_container.count == 3
        assert restored_string_container.items == ["apple", "banana", "cherry"]

        # Verify int container
        assert restored_int_container.name == "numbers"
        assert restored_int_container.count == 5
        assert restored_int_container.items == [1, 2, 3, 4, 5]

        print("✅ Simple generic container serialization successful with normal import!")

    def test_simple_generic_container(self):
        """Test basic generic container with single type parameter."""

        class Container(BaseModel, Generic[T]):
            """A generic container that can hold any type."""

            items: List[T]
            name: str
            count: int

            def get_summary(self) -> str:
                return f"Container '{self.name}' with {self.count} items"

        # Set fake module name to force class registry usage
        Container.__module__ = "test.fake.module"

        # Create instances with different concrete types
        string_container = Container[str](items=["apple", "banana", "cherry"], name="fruit_basket", count=3)

        int_container = Container[int](items=[1, 2, 3, 4, 5], name="numbers", count=5)

        print(f"String container: {string_container.get_summary()}")
        print(f"String items: {string_container.items}")
        print(f"Int container: {int_container.get_summary()}")
        print(f"Int items: {int_container.items}")

        # Serialize both containers
        string_json = kajson.dumps(string_container)
        int_json = kajson.dumps(int_container)

        print(f"\nString container JSON: {string_json}")
        print(f"Int container JSON: {int_json}")

        # Register class for deserialization
        registry = KajsonManager.get_class_registry()
        registry.register_class(Container)

        try:
            # Deserialize and verify
            restored_string_container = kajson.loads(string_json)
            restored_int_container = kajson.loads(int_json)

            print(f"\nRestored string container: {restored_string_container.get_summary()}")
            print(f"Restored string items: {restored_string_container.items}")
            print(f"Restored int container: {restored_int_container.get_summary()}")
            print(f"Restored int items: {restored_int_container.items}")

            # Verify string container
            assert restored_string_container.name == "fruit_basket"
            assert restored_string_container.count == 3
            assert restored_string_container.items == ["apple", "banana", "cherry"]

            # Verify int container
            assert restored_int_container.name == "numbers"
            assert restored_int_container.count == 5
            assert restored_int_container.items == [1, 2, 3, 4, 5]

            print("✅ Simple generic container serialization successful!")
        finally:
            registry.teardown()

    def test_generic_key_value_store(self):
        """Test generic model with multiple type parameters."""

        class KeyValueStore(BaseModel, Generic[K, V]):
            """A generic key-value store."""

            store_name: str
            data: Dict[K, V]
            created_by: str

            def get_keys(self) -> List[K]:
                return list(self.data.keys())

            def get_values(self) -> List[V]:
                return list(self.data.values())

        # Set fake module name
        KeyValueStore.__module__ = "test.fake.module"

        # Create instances with different key-value type combinations
        string_int_store = KeyValueStore[str, int](store_name="user_scores", data={"alice": 95, "bob": 87, "charlie": 92}, created_by="admin")

        int_string_store = KeyValueStore[int, str](
            store_name="error_messages", data={404: "Not Found", 500: "Internal Server Error", 403: "Forbidden"}, created_by="system"
        )

        print(f"String-Int store: {string_int_store.store_name}")
        print(f"Keys: {string_int_store.get_keys()}")
        print(f"Values: {string_int_store.get_values()}")

        print(f"\nInt-String store: {int_string_store.store_name}")
        print(f"Keys: {int_string_store.get_keys()}")
        print(f"Values: {int_string_store.get_values()}")

        # Serialize
        string_int_json = kajson.dumps(string_int_store)
        int_string_json = kajson.dumps(int_string_store)

        print(f"\nString-Int JSON: {string_int_json}")
        print(f"Int-String JSON: {int_string_json}")

        # Register class
        registry = KajsonManager.get_class_registry()
        registry.register_class(KeyValueStore)

        try:
            # Deserialize
            restored_string_int = kajson.loads(string_int_json)
            restored_int_string = kajson.loads(int_string_json)

            print(f"\nRestored String-Int store: {restored_string_int.store_name}")
            print(f"Restored keys: {restored_string_int.get_keys()}")
            print(f"Restored values: {restored_string_int.get_values()}")

            # Verify string-int store
            assert restored_string_int.store_name == "user_scores"
            assert restored_string_int.created_by == "admin"
            assert restored_string_int.data == {"alice": 95, "bob": 87, "charlie": 92}

            # Verify int-string store
            assert restored_int_string.store_name == "error_messages"
            assert restored_int_string.created_by == "system"
            # Note: JSON converts integer keys to strings, so we expect string keys
            assert restored_int_string.data == {"404": "Not Found", "500": "Internal Server Error", "403": "Forbidden"}

            print("✅ Generic key-value store serialization successful!")
        finally:
            registry.teardown()

    def test_nested_generic_models(self):
        """Test nesting generic models within other generic models."""

        class Node(BaseModel, Generic[T]):
            """A generic tree node."""

            value: T
            children: List["Node[T]"] = Field(default_factory=list)
            metadata: Optional[Dict[str, str]] = None

            def add_child(self, child: "Node[T]") -> None:
                self.children.append(child)

            def count_nodes(self) -> int:
                return 1 + sum(child.count_nodes() for child in self.children)

        class Tree(BaseModel, Generic[T]):
            """A generic tree structure."""

            name: str
            root: Optional[Node[T]] = None

            def get_node_count(self) -> int:
                return self.root.count_nodes() if self.root else 0

        # Set fake module names
        Node.__module__ = "test.fake.module"
        Tree.__module__ = "test.fake.module"

        # Create a tree of strings
        root_node = Node[str](value="root", metadata={"type": "root", "level": "0"})

        child1 = Node[str](value="child1", metadata={"type": "branch", "level": "1"})

        child2 = Node[str](value="child2", metadata={"type": "branch", "level": "1"})

        grandchild1 = Node[str](value="grandchild1", metadata={"type": "leaf", "level": "2"})

        child1.add_child(grandchild1)
        root_node.add_child(child1)
        root_node.add_child(child2)

        string_tree = Tree[str](name="family_tree", root=root_node)

        print(f"String tree: {string_tree.name}")
        print(f"Node count: {string_tree.get_node_count()}")
        print(f"Root value: {string_tree.root.value if string_tree.root else None}")
        print(f"Children: {[child.value for child in string_tree.root.children] if string_tree.root else []}")

        # Serialize
        tree_json = kajson.dumps(string_tree)
        print(f"\nTree JSON length: {len(tree_json)} characters")

        # Register classes
        registry = KajsonManager.get_class_registry()
        registry.register_class(Node)
        registry.register_class(Tree)

        try:
            # Deserialize
            restored_tree = kajson.loads(tree_json)

            print(f"\nRestored tree: {restored_tree.name}")
            print(f"Restored node count: {restored_tree.get_node_count()}")
            print(f"Restored root value: {restored_tree.root.value if restored_tree.root else None}")
            print(f"Restored children: {[child.value for child in restored_tree.root.children] if restored_tree.root else []}")

            # Verify structure
            assert restored_tree.name == "family_tree"
            assert restored_tree.get_node_count() == 4
            assert restored_tree.root is not None
            assert restored_tree.root.value == "root"
            assert len(restored_tree.root.children) == 2
            assert restored_tree.root.children[0].value == "child1"
            assert restored_tree.root.children[1].value == "child2"
            assert len(restored_tree.root.children[0].children) == 1
            assert restored_tree.root.children[0].children[0].value == "grandchild1"

            # Verify metadata
            assert restored_tree.root.metadata is not None
            assert restored_tree.root.metadata["type"] == "root"
            assert restored_tree.root.children[0].metadata is not None
            assert restored_tree.root.children[0].metadata["level"] == "1"

            print("✅ Nested generic models serialization successful!")
        finally:
            registry.teardown()

    def test_generic_model_with_union_types(self):
        """Test generic models that use Union types within their type parameters."""

        class Response(BaseModel, Generic[T]):
            """A generic API response."""

            success: bool
            data: Optional[T] = None
            error: Optional[str] = None
            timestamp: str

            def is_successful(self) -> bool:
                return self.success and self.data is not None

        class User(BaseModel):
            """User model for testing."""

            id: int
            name: str
            email: str

        class Product(BaseModel):
            """Product model for testing."""

            id: int
            name: str
            price: float

        # Set fake module names
        Response.__module__ = "test.fake.module"
        User.__module__ = "test.fake.module"
        Product.__module__ = "test.fake.module"

        # Create responses with different data types
        user_response = Response[User](success=True, data=User(id=1, name="Alice", email="alice@example.com"), timestamp="2025-01-15T10:30:00Z")

        product_list_response = Response[List[Product]](
            success=True,
            data=[Product(id=1, name="Widget", price=19.99), Product(id=2, name="Gadget", price=29.99)],
            timestamp="2025-01-15T10:35:00Z",
        )

        error_response = Response[str](success=False, error="User not found", timestamp="2025-01-15T10:40:00Z")

        print(f"User response successful: {user_response.is_successful()}")
        print(f"User data: {user_response.data}")

        print(f"\nProduct list response successful: {product_list_response.is_successful()}")
        print(f"Product count: {len(product_list_response.data) if product_list_response.data else 0}")

        print(f"\nError response successful: {error_response.is_successful()}")
        print(f"Error message: {error_response.error}")

        # Serialize
        user_json = kajson.dumps(user_response)
        product_json = kajson.dumps(product_list_response)
        error_json = kajson.dumps(error_response)

        print(f"\nUser response JSON: {user_json}")
        print(f"Product response JSON: {product_json}")
        print(f"Error response JSON: {error_json}")

        # Register classes
        registry = KajsonManager.get_class_registry()
        registry.register_class(Response)
        registry.register_class(User)
        registry.register_class(Product)

        try:
            # Deserialize
            restored_user_response = kajson.loads(user_json)
            restored_product_response = kajson.loads(product_json)
            restored_error_response = kajson.loads(error_json)

            print(f"\nRestored user response successful: {restored_user_response.is_successful()}")
            print(f"Restored user data: {restored_user_response.data}")

            # Verify user response
            assert restored_user_response.success is True
            assert restored_user_response.data is not None
            assert restored_user_response.data.id == 1
            assert restored_user_response.data.name == "Alice"
            assert restored_user_response.data.email == "alice@example.com"

            # Verify product response
            assert restored_product_response.success is True
            assert restored_product_response.data is not None
            assert len(restored_product_response.data) == 2
            assert restored_product_response.data[0].name == "Widget"
            assert restored_product_response.data[1].price == 29.99

            # Verify error response
            assert restored_error_response.success is False
            assert restored_error_response.error == "User not found"
            assert restored_error_response.data is None

            print("✅ Generic models with union types serialization successful!")
        finally:
            registry.teardown()

    def test_bounded_generic_models(self):
        """Test generic models with bounded type parameters."""

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

        # Type variable bounded to Numeric
        NumericType = TypeVar("NumericType", bound=Numeric)

        class Calculator(BaseModel, Generic[NumericType]):
            """A generic calculator that works with numeric types."""

            name: str
            operands: List[NumericType]

            def sum_values(self) -> Union[int, float]:
                return sum(operand.get_value() for operand in self.operands)

        # Set fake module names
        Numeric.__module__ = "test.fake.module"
        IntegerValue.__module__ = "test.fake.module"
        FloatValue.__module__ = "test.fake.module"
        Calculator.__module__ = "test.fake.module"

        # Create calculators with different numeric types
        int_calculator = Calculator[IntegerValue](
            name="integer_calculator", operands=[IntegerValue(value=10), IntegerValue(value=20), IntegerValue(value=30)]
        )

        float_calculator = Calculator[FloatValue](
            name="float_calculator", operands=[FloatValue(value=10.5), FloatValue(value=20.7), FloatValue(value=30.2)]
        )

        print(f"Int calculator sum: {int_calculator.sum_values()}")
        print(f"Float calculator sum: {float_calculator.sum_values()}")

        # Serialize
        int_json = kajson.dumps(int_calculator)
        float_json = kajson.dumps(float_calculator)

        print(f"\nInt calculator JSON: {int_json}")
        print(f"Float calculator JSON: {float_json}")

        # Register classes
        registry = KajsonManager.get_class_registry()
        registry.register_class(Numeric)
        registry.register_class(IntegerValue)
        registry.register_class(FloatValue)
        registry.register_class(Calculator)

        try:
            # Deserialize
            restored_int_calc = kajson.loads(int_json)
            restored_float_calc = kajson.loads(float_json)

            print(f"\nRestored int calculator sum: {restored_int_calc.sum_values()}")
            print(f"Restored float calculator sum: {restored_float_calc.sum_values()}")

            # Verify int calculator
            assert restored_int_calc.name == "integer_calculator"
            assert len(restored_int_calc.operands) == 3
            assert restored_int_calc.sum_values() == 60
            assert all(isinstance(op, IntegerValue) for op in restored_int_calc.operands)

            # Verify float calculator
            assert restored_float_calc.name == "float_calculator"
            assert len(restored_float_calc.operands) == 3
            assert abs(restored_float_calc.sum_values() - 61.4) < 0.01
            assert all(isinstance(op, FloatValue) for op in restored_float_calc.operands)

            print("✅ Bounded generic models serialization successful!")
        finally:
            registry.teardown()
