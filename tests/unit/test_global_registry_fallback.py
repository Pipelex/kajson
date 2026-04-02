# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Generator, Type

import pytest
from pydantic import BaseModel

import kajson
from kajson.class_registry import ClassRegistry
from kajson.exceptions import KajsonDecoderError
from kajson.kajson_manager import KajsonManager


def _make_dynamic_class(name: str) -> Type[BaseModel]:
    """Create a dynamic BaseModel subclass with __module__='builtins', simulating exec()-generated classes."""
    namespace: dict[str, Any] = {}
    source = f"""
from pydantic import BaseModel

class {name}(BaseModel):
    greeting: str
"""
    exec(compile(source, "<test>", "exec"), namespace)
    dynamic_cls: Type[BaseModel] = namespace[name]
    assert dynamic_cls.__module__ == "builtins"
    return dynamic_cls


class TestGlobalRegistryFallback:
    """Tests that the decoder falls through to the global KajsonManager registry
    when sys.modules lookup finds the module but not the class."""

    @pytest.fixture(autouse=True)
    def _setup_teardown(self) -> Generator[None, None, None]:
        """Ensure the global KajsonManager singleton is torn down after each test."""
        yield
        KajsonManager.teardown()

    def test_global_registry_resolves_builtins_class_without_explicit_registry(self) -> None:
        """When __module__='builtins' and no explicit registry is passed,
        the decoder should fall through from sys.modules to the global KajsonManager registry."""
        dynamic_cls = _make_dynamic_class("DynamicConceptTestGreeting")
        KajsonManager.get_class_registry().register_class(dynamic_cls)

        json_str = '{"__class__": "DynamicConceptTestGreeting", "__module__": "builtins", "greeting": "Hello"}'

        result = kajson.loads(json_str)
        assert isinstance(result, BaseModel)
        assert result.__class__.__name__ == "DynamicConceptTestGreeting"
        assert result.greeting == "Hello"  # type: ignore[attr-defined]

    def test_explicit_registry_still_takes_priority_over_global(self) -> None:
        """When both explicit and global registries have the class,
        the explicit registry wins (Step 0 before Step 1/2)."""
        dynamic_cls = _make_dynamic_class("PriorityTestModel")
        KajsonManager.get_class_registry().register_class(dynamic_cls)

        class ExplicitModel(BaseModel):
            greeting: str
            source: str = "explicit"

        explicit_registry = ClassRegistry()
        explicit_registry.register_class(ExplicitModel, name="PriorityTestModel")

        json_str = '{"__class__": "PriorityTestModel", "__module__": "builtins", "greeting": "Hello"}'

        result = kajson.loads(json_str, class_registry=explicit_registry)
        assert isinstance(result, ExplicitModel)
        assert result.source == "explicit"

    def test_raises_when_class_in_neither_module_nor_global_registry(self) -> None:
        """When the class is not in sys.modules['builtins'] and not in the global registry,
        the decoder should raise KajsonDecoderError."""
        json_str = '{"__class__": "CompletelyUnknownClass", "__module__": "builtins", "greeting": "Hello"}'

        with pytest.raises(KajsonDecoderError, match="not found in module 'builtins' or global registry"):
            kajson.loads(json_str)
