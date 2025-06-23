# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, List, Optional, Type

import pytest
from typing_extensions import override

from kajson.class_registry import ClassRegistry
from kajson.class_registry_abstract import ClassRegistryAbstract
from kajson.kajson_manager import KAJSON_LOGGER_CHANNEL_NAME, KajsonManager


class TestKajsonManager:
    def test_true_singleton_pattern(self):
        """Test that KajsonManager follows true singleton pattern."""
        # Initially no instance should exist
        KajsonManager.teardown()

        # Create first instance
        manager1 = KajsonManager()

        # Attempt to create second instance should raise RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            KajsonManager()
        assert "KajsonManager is already initialized" in str(excinfo.value)

        # get_instance should return the first (and only) instance
        retrieved_manager = KajsonManager.get_instance()
        assert retrieved_manager is manager1

        # Cleanup
        KajsonManager.teardown()

    def test_get_instance_success(self):
        """Test successful get_instance call."""
        # The conftest.py fixture already created an instance
        retrieved_manager = KajsonManager.get_instance()
        assert retrieved_manager is not None

        # Test that get_instance always returns the same instance
        second_retrieved = KajsonManager.get_instance()
        assert retrieved_manager is second_retrieved

    def test_get_instance_not_initialized(self):
        """Test get_instance when not initialized raises RuntimeError."""
        KajsonManager.teardown()

        with pytest.raises(RuntimeError) as excinfo:
            KajsonManager.get_instance()
        assert "KajsonManager is not initialized" in str(excinfo.value)

    def test_initialization_default_values(self):
        """Test initialization with default values."""
        # The conftest.py fixture already created an instance with defaults
        manager = KajsonManager.get_instance()

        # Test that defaults were used
        assert manager.logger_channel_name == KAJSON_LOGGER_CHANNEL_NAME
        assert isinstance(KajsonManager.get_class_registry(), ClassRegistry)

    def test_initialization_custom_values(self):
        """Test initialization with custom values."""
        custom_logger_name = "custom.logger"
        custom_registry = ClassRegistry()

        # Teardown the existing instance first
        KajsonManager.teardown()

        KajsonManager(logger_channel_name=custom_logger_name, class_registry=custom_registry)

        # Verify the custom values were set
        manager = KajsonManager.get_instance()
        assert manager.logger_channel_name == custom_logger_name
        assert KajsonManager.get_class_registry() is custom_registry

    def test_initialization_none_values(self):
        """Test initialization with None values uses defaults."""
        # Teardown the existing instance first
        KajsonManager.teardown()

        KajsonManager(logger_channel_name=None, class_registry=None)

        # Verify default values were used
        manager = KajsonManager.get_instance()
        assert manager.logger_channel_name == KAJSON_LOGGER_CHANNEL_NAME
        assert isinstance(KajsonManager.get_class_registry(), ClassRegistry)

    def test_teardown(self):
        """Test teardown method clears the singleton instance."""
        # Confirm instance exists (created by conftest.py)
        assert KajsonManager.get_instance() is not None

        KajsonManager.teardown()

        # After teardown, get_instance should fail
        with pytest.raises(RuntimeError):
            KajsonManager.get_instance()

    def test_get_class_registry_success(self):
        """Test successful get_class_registry call."""
        custom_registry = ClassRegistry()

        # Teardown the existing instance first
        KajsonManager.teardown()
        KajsonManager(class_registry=custom_registry)

        retrieved_registry = KajsonManager.get_class_registry()
        assert retrieved_registry is custom_registry

    def test_get_class_registry_not_initialized(self):
        """Test get_class_registry when not initialized raises RuntimeError."""
        KajsonManager.teardown()

        with pytest.raises(RuntimeError) as excinfo:
            KajsonManager.get_class_registry()
        assert "KajsonManager is not initialized" in str(excinfo.value)

    def test_multiple_initialization_attempts(self):
        """Test that attempting multiple initializations raises RuntimeError."""
        # An instance already exists from conftest.py
        # Second initialization attempt should raise RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            KajsonManager(logger_channel_name="second.logger")
        assert "KajsonManager is already initialized" in str(excinfo.value)

        # get_instance should still return the original instance
        retrieved_manager = KajsonManager.get_instance()
        assert retrieved_manager is not None
        assert retrieved_manager.logger_channel_name == KAJSON_LOGGER_CHANNEL_NAME

    def test_class_registry_integration(self):
        """Test integration with ClassRegistry."""
        # Use the existing instance or create custom one
        retrieved_registry = KajsonManager.get_class_registry()

        # Register a class through the manager's registry
        retrieved_registry.register_class(str, "String")

        # Verify the class is registered
        assert retrieved_registry.has_class("String")
        assert retrieved_registry.get_class("String") is str

    def test_custom_class_registry_abstract(self):
        """Test with custom ClassRegistryAbstract implementation."""

        class MockClassRegistry(ClassRegistryAbstract):
            def __init__(self):
                self.classes: Dict[str, Type[Any]] = {}

            @override
            def setup(self) -> None:
                pass

            @override
            def teardown(self) -> None:
                self.classes.clear()

            @override
            def register_class(
                self,
                class_type: Type[Any],
                name: Optional[str] = None,
                should_warn_if_already_registered: bool = True,
            ) -> None:
                self.classes[name or class_type.__name__] = class_type

            @override
            def unregister_class(self, class_type: Type[Any]) -> None:
                pass

            @override
            def unregister_class_by_name(self, name: str) -> None:
                pass

            @override
            def register_classes_dict(self, classes: Dict[str, Type[Any]]) -> None:
                pass

            @override
            def register_classes(self, classes: List[Type[Any]]) -> None:
                pass

            @override
            def get_class(self, name: str) -> Optional[Type[Any]]:
                return self.classes.get(name)

            @override
            def get_required_class(self, name: str) -> Type[Any]:
                return self.classes[name]

            @override
            def get_required_subclass(self, name: str, base_class: Type[Any]) -> Type[Any]:
                return self.classes[name]

            @override
            def get_required_base_model(self, name: str) -> Type[Any]:
                return self.classes[name]

            @override
            def has_class(self, name: str) -> bool:
                return name in self.classes

            @override
            def has_subclass(self, name: str, base_class: Type[Any]) -> bool:
                return name in self.classes

        mock_registry = MockClassRegistry()

        # Teardown the existing instance first
        KajsonManager.teardown()
        KajsonManager(class_registry=mock_registry)

        # Test that the custom registry is used
        retrieved_registry = KajsonManager.get_class_registry()
        assert retrieved_registry is mock_registry

        # Test functionality with custom registry
        retrieved_registry.register_class(str, "String")
        assert retrieved_registry.has_class("String")

    def test_teardown_and_reinitialization(self):
        """Test teardown works correctly and allows reinitialization."""
        # Get the existing instance (from conftest.py)
        manager1 = KajsonManager.get_instance()

        # get_instance should return the singleton instance
        assert KajsonManager.get_instance() is manager1

        # Teardown should clear the instance
        KajsonManager.teardown()

        # After teardown, get_instance should fail
        with pytest.raises(RuntimeError):
            KajsonManager.get_instance()

        # Should be able to create a new instance after teardown
        manager2 = KajsonManager()
        assert manager2 is not manager1

        # New instance should be available via get_instance
        assert KajsonManager.get_instance() is manager2

    def test_logger_channel_name_persistence(self):
        """Test that logger_channel_name persists across get_instance calls."""
        custom_name = "persistent.logger"

        # Teardown the existing instance first
        KajsonManager.teardown()
        KajsonManager(logger_channel_name=custom_name)

        # Get instance multiple times
        retrieved1 = KajsonManager.get_instance()
        retrieved2 = KajsonManager.get_instance()

        # All should have the same logger_channel_name
        assert retrieved1.logger_channel_name == custom_name
        assert retrieved2.logger_channel_name == custom_name
        # They should be the same object (singleton)
        assert retrieved1 is retrieved2

    def test_class_registry_persistence(self):
        """Test that class_registry persists across get_instance calls."""
        custom_registry = ClassRegistry()

        # Teardown the existing instance first
        KajsonManager.teardown()
        KajsonManager(class_registry=custom_registry)

        # Multiple calls should return the same class_registry
        registry1 = KajsonManager.get_class_registry()
        registry2 = KajsonManager.get_class_registry()

        assert registry1 is custom_registry
        assert registry2 is custom_registry
        assert registry1 is registry2
