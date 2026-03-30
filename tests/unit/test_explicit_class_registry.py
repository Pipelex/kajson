# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel

import kajson
from kajson.class_registry import ClassRegistry


class DynamicModel(BaseModel):
    """A model that simulates a dynamically generated class (like concept structure classes)."""

    greeting: str


class TestExplicitClassRegistry:
    def test_loads_with_explicit_registry_resolves_dynamic_class(self) -> None:
        """kajson.loads() with explicit class_registry finds classes even when __module__ is 'builtins'.

        This is the exact bug scenario: dynamically generated classes have __module__='builtins',
        so the decoder finds 'builtins' in sys.modules but the class isn't there. The explicit
        registry bypasses that path entirely.
        """
        registry = ClassRegistry()
        registry.register_class(DynamicModel)

        json_str = '{"__class__": "DynamicModel", "__module__": "builtins", "greeting": "Hello"}'

        result = kajson.loads(json_str, class_registry=registry)
        assert isinstance(result, DynamicModel)
        assert result.greeting == "Hello"

    def test_explicit_registry_takes_priority_over_sys_modules(self) -> None:
        """When a class exists in both the explicit registry AND sys.modules,
        the explicit registry version is used."""
        # DynamicModel is available in this test module's sys.modules
        # Register a different class under the same name in the explicit registry

        class AlternativeModel(BaseModel):
            greeting: str
            extra: str = "from_registry"

        registry = ClassRegistry()
        registry.register_class(AlternativeModel, name="DynamicModel")

        json_str = f'{{"__class__": "DynamicModel", "__module__": "{DynamicModel.__module__}", "greeting": "Hello"}}'

        result = kajson.loads(json_str, class_registry=registry)
        assert isinstance(result, AlternativeModel)
        assert result.greeting == "Hello"
        assert result.extra == "from_registry"

    def test_loads_without_explicit_registry_uses_sys_modules(self) -> None:
        """Without explicit class_registry, loads() falls back to sys.modules as before."""
        json_str = kajson.dumps(DynamicModel(greeting="Hello"))
        result = kajson.loads(json_str)
        assert isinstance(result, DynamicModel)
        assert result.greeting == "Hello"

    def test_load_with_explicit_registry_resolves_dynamic_class(self) -> None:
        """kajson.load() with explicit class_registry works the same as loads()."""
        import io

        registry = ClassRegistry()
        registry.register_class(DynamicModel)

        json_str = '{"__class__": "DynamicModel", "__module__": "builtins", "greeting": "Hello"}'

        result = kajson.load(io.StringIO(json_str), class_registry=registry)
        assert isinstance(result, DynamicModel)
        assert result.greeting == "Hello"

    def test_loads_with_explicit_registry_falls_through_on_miss(self) -> None:
        """If explicit registry doesn't have the class, decoder falls through to sys.modules."""
        empty_registry = ClassRegistry()

        json_str = kajson.dumps(DynamicModel(greeting="Hello"))
        result = kajson.loads(json_str, class_registry=empty_registry)
        assert isinstance(result, DynamicModel)
        assert result.greeting == "Hello"
