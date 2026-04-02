# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import io
from typing import Any, cast

from pydantic import BaseModel

import kajson
from kajson.class_registry import ClassRegistry


class ModuleLevelModel(BaseModel):
    value: int


SIMPLE_MODEL_SOURCE = """
from pydantic import BaseModel, Field

class Greeting(BaseModel):
    message: str = Field(..., title="Message")
    count: int = Field(..., title="Count")
"""

NESTED_MODEL_SOURCE = """
from pydantic import BaseModel, Field

class Address(BaseModel):
    street: str = Field(..., title="Street")
    city: str = Field(..., title="City")

class Person(BaseModel):
    name: str = Field(..., title="Name")
    address: Address
"""


class TestClassSourceCode:
    def test_loads_with_class_source_code_simple(self) -> None:
        """kajson.loads() with class_source_code resolves a simple model."""
        json_str = '{"__class__": "Greeting", "__module__": "builtins", "message": "Hello", "count": 3}'

        result = kajson.loads(json_str, class_source_code=SIMPLE_MODEL_SOURCE)
        assert result.__class__.__name__ == "Greeting"
        assert result.message == "Hello"
        assert result.count == 3

    def test_loads_with_class_source_code_nested(self) -> None:
        """kajson.loads() with class_source_code resolves nested models from the same source."""
        json_str = (
            '{"__class__": "Person", "__module__": "builtins", '
            '"name": "Alice", '
            '"address": {"__class__": "Address", "__module__": "builtins", "street": "123 Main", "city": "NYC"}}'
        )

        result = kajson.loads(json_str, class_source_code=NESTED_MODEL_SOURCE)
        assert result.__class__.__name__ == "Person"
        assert result.name == "Alice"
        assert result.address.__class__.__name__ == "Address"
        assert result.address.city == "NYC"

    def test_explicit_registry_takes_priority_over_source(self) -> None:
        """When both class_registry and class_source_code are provided, explicit registry wins."""

        class OverrideGreeting(BaseModel):
            message: str
            count: int
            extra: str = "from_registry"

        registry = ClassRegistry()
        registry.register_class(OverrideGreeting, name="Greeting")

        json_str = '{"__class__": "Greeting", "__module__": "builtins", "message": "Hello", "count": 3}'

        result = kajson.loads(json_str, class_registry=registry, class_source_code=SIMPLE_MODEL_SOURCE)
        assert isinstance(result, OverrideGreeting)
        assert result.extra == "from_registry"

    def test_source_fills_gaps_in_explicit_registry(self) -> None:
        """class_source_code provides classes not in the explicit registry."""

        class CustomPerson(BaseModel):
            name: str
            address: BaseModel  # type: ignore[assignment]

        registry = ClassRegistry()
        # Register Person but NOT Address — Address should come from source
        registry.register_class(CustomPerson, name="Person")

        json_str = (
            '{"__class__": "Person", "__module__": "builtins", '
            '"name": "Bob", '
            '"address": {"__class__": "Address", "__module__": "builtins", "street": "456 Oak", "city": "LA"}}'
        )

        result = kajson.loads(json_str, class_registry=registry, class_source_code=NESTED_MODEL_SOURCE)
        # Person comes from explicit registry
        assert isinstance(result, CustomPerson)
        # Address comes from source code — access dynamically since it's resolved at runtime
        address: Any = result.address
        assert address.__class__.__name__ == "Address"
        assert address.city == "LA"

    def test_loads_without_source_unchanged(self) -> None:
        """Without class_source_code, loads() behaves exactly as before."""
        json_str = kajson.dumps(ModuleLevelModel(value=42))
        result = kajson.loads(json_str)
        assert isinstance(result, ModuleLevelModel)
        assert result.value == 42

    def test_load_with_class_source_code(self) -> None:
        """kajson.load() also supports class_source_code."""
        json_str = '{"__class__": "Greeting", "__module__": "builtins", "message": "Hi", "count": 1}'

        result = kajson.load(io.StringIO(json_str), class_source_code=SIMPLE_MODEL_SOURCE)
        assert result.__class__.__name__ == "Greeting"
        assert result.message == "Hi"

    def test_caller_registry_not_mutated_by_source_code(self) -> None:
        """Caller's registry must not be polluted with source-derived classes."""
        registry = ClassRegistry()
        registry.register_class(ModuleLevelModel, name="ModuleLevelModel")

        json_str = '{"__class__": "Greeting", "__module__": "builtins", "message": "Hi", "count": 1}'
        kajson.loads(json_str, class_registry=registry, class_source_code=SIMPLE_MODEL_SOURCE)

        # Registry should still only contain the originally registered class
        assert registry.has_class("ModuleLevelModel")
        assert not registry.has_class("Greeting")
        assert not registry.has_class("count")

    def test_list_with_class_source_code(self) -> None:
        """class_source_code works for deserializing lists of BaseModel."""
        json_str = (
            '[{"__class__": "Greeting", "__module__": "builtins", "message": "A", "count": 1}, '
            '{"__class__": "Greeting", "__module__": "builtins", "message": "B", "count": 2}]'
        )

        raw_result = kajson.loads(json_str, class_source_code=SIMPLE_MODEL_SOURCE)
        assert isinstance(raw_result, list)
        result = cast(list[Any], raw_result)
        assert len(result) == 2
        assert result[0].__class__.__name__ == "Greeting"
        assert result[0].message == "A"
        assert result[1].message == "B"
