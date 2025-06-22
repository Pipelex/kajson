# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0


import pytest
from pydantic import BaseModel
from pytest_mock import MockerFixture

from kajson.class_registry import ClassRegistry
from kajson.exceptions import ClassRegistryInheritanceError, ClassRegistryNotFoundError


class TestClassRegistry:
    def test_setup_and_teardown(self):
        """Test setup and teardown methods."""
        registry = ClassRegistry()

        # Setup should pass without errors
        registry.setup()

        # Add some classes
        registry.register_class(str)
        registry.register_class(int)
        assert registry.has_class("str")
        assert registry.has_class("int")

        # Teardown should clear the registry
        registry.teardown()
        assert not registry.has_class("str")
        assert not registry.has_class("int")
        assert len(registry.root) == 0

    def test_register_class_basic(self):
        """Test basic class registration."""
        registry = ClassRegistry()

        # Register with default name
        registry.register_class(str)
        assert registry.has_class("str")
        assert registry.get_class("str") is str

        # Register with custom name
        registry.register_class(int, "Integer")
        assert registry.has_class("Integer")
        assert registry.get_class("Integer") is int

    def test_register_class_duplicate_warning(self, mocker: MockerFixture):
        """Test duplicate class registration with warning."""
        registry = ClassRegistry()
        mock_logger = mocker.MagicMock()
        registry.set_logger(mock_logger)

        # First registration
        registry.register_class(str)

        # Second registration should warn
        registry.register_class(str, should_warn_if_already_registered=True)
        mock_logger.debug.assert_called_with("Class 'None' already exists in registry")

        # Third registration without warning
        registry.register_class(str, should_warn_if_already_registered=False)

    def test_unregister_class(self):
        """Test class unregistration."""
        registry = ClassRegistry()

        # Register a class
        registry.register_class(str)
        assert registry.has_class("str")

        # Unregister it
        registry.unregister_class(str)
        assert not registry.has_class("str")

        # Try to unregister non-existent class
        with pytest.raises(ClassRegistryNotFoundError) as excinfo:
            registry.unregister_class(int)
        assert "Class 'int' not found in registry" in str(excinfo.value)

    def test_unregister_class_by_name(self):
        """Test class unregistration by name."""
        registry = ClassRegistry()

        # Register a class
        registry.register_class(str, "String")
        assert registry.has_class("String")

        # Unregister by name
        registry.unregister_class_by_name("String")
        assert not registry.has_class("String")

        # Try to unregister non-existent class
        with pytest.raises(ClassRegistryNotFoundError) as excinfo:
            registry.unregister_class_by_name("NonExistent")
        assert "Class 'NonExistent' not found in registry" in str(excinfo.value)

    def test_register_classes_dict(self, mocker: MockerFixture):
        """Test registering multiple classes via dictionary."""
        registry = ClassRegistry()
        mock_logger = mocker.MagicMock()
        registry.set_logger(mock_logger)

        classes_dict = {"String": str, "Integer": int, "Float": float}

        registry.register_classes_dict(classes_dict)

        # Check all classes are registered
        assert registry.has_class("String")
        assert registry.has_class("Integer")
        assert registry.has_class("Float")
        assert registry.get_class("String") is str
        assert registry.get_class("Integer") is int
        assert registry.get_class("Float") is float

        # Check logging
        mock_logger.debug.assert_called_with("Registered 3 classes in registry")

    def test_register_classes_dict_single(self, mocker: MockerFixture):
        """Test registering single class via dictionary."""
        registry = ClassRegistry()
        mock_logger = mocker.MagicMock()
        registry.set_logger(mock_logger)

        classes_dict = {"String": str}
        registry.register_classes_dict(classes_dict)

        assert registry.has_class("String")
        mock_logger.debug.assert_called_with("Registered single class 'str' in registry")

    def test_register_classes_list(self, mocker: MockerFixture):
        """Test registering multiple classes via list."""
        registry = ClassRegistry()
        mock_logger = mocker.MagicMock()
        registry.set_logger(mock_logger)

        classes_list = [str, int, float]
        registry.register_classes(classes_list)

        # Check all classes are registered
        assert registry.has_class("str")
        assert registry.has_class("int")
        assert registry.has_class("float")

        # Check logging
        mock_logger.debug.assert_called_with("Registered 3 classes in registry")

    def test_register_classes_list_empty(self, mocker: MockerFixture):
        """Test registering empty list of classes."""
        registry = ClassRegistry()
        mock_logger = mocker.MagicMock()
        registry.set_logger(mock_logger)

        registry.register_classes([])

        mock_logger.debug.assert_called_with("register_classes called with empty list of classes to register")

    def test_register_classes_list_single(self, mocker: MockerFixture):
        """Test registering single class via list."""
        registry = ClassRegistry()
        mock_logger = mocker.MagicMock()
        registry.set_logger(mock_logger)

        registry.register_classes([str])

        assert registry.has_class("str")
        mock_logger.debug.assert_called_with("Registered single class 'str' in registry")

    def test_register_classes_list_duplicate(self, mocker: MockerFixture):
        """Test registering classes with duplicates."""
        registry = ClassRegistry()
        mock_logger = mocker.MagicMock()
        registry.set_logger(mock_logger)

        # Register str first
        registry.register_class(str)

        # Try to register list including str
        registry.register_classes([str, int])

        # Should skip str and register int
        mock_logger.debug.assert_any_call("Class 'str' already exists in registry, skipping")
        assert registry.has_class("str")
        assert registry.has_class("int")

    def test_get_class(self):
        """Test getting class from registry."""
        registry = ClassRegistry()

        registry.register_class(str)

        # Existing class
        assert registry.get_class("str") is str

        # Non-existing class
        assert registry.get_class("NonExistent") is None

    def test_get_required_class(self):
        """Test getting required class from registry."""
        registry = ClassRegistry()

        registry.register_class(str)

        # Existing class
        assert registry.get_required_class("str") is str

        # Non-existing class
        with pytest.raises(ClassRegistryNotFoundError) as excinfo:
            registry.get_required_class("NonExistent")
        assert "Class 'NonExistent' not found in registry" in str(excinfo.value)

    def test_get_required_subclass(self):
        """Test getting required subclass from registry."""
        registry = ClassRegistry()

        # Create test classes
        class TestBase:
            pass

        class TestChild(TestBase):
            pass

        class TestUnrelated:
            pass

        registry.register_class(TestChild)
        registry.register_class(TestUnrelated)

        # Valid subclass
        assert registry.get_required_subclass("TestChild", TestBase) is TestChild

        # Invalid subclass
        with pytest.raises(ClassRegistryInheritanceError) as excinfo:
            registry.get_required_subclass("TestUnrelated", TestBase)
        assert "is not a subclass of" in str(excinfo.value)

        # Non-existing class
        with pytest.raises(ClassRegistryNotFoundError) as excinfo:
            registry.get_required_subclass("NonExistent", TestBase)
        assert "Class 'NonExistent' not found in registry" in str(excinfo.value)

    def test_get_required_base_model(self):
        """Test getting required BaseModel from registry."""
        registry = ClassRegistry()

        # Create test classes
        class TestModel(BaseModel):
            name: str

        class TestNonModel:
            pass

        registry.register_class(TestModel)
        registry.register_class(TestNonModel)

        # Valid BaseModel
        assert registry.get_required_base_model("TestModel") is TestModel

        # Invalid BaseModel
        with pytest.raises(ClassRegistryInheritanceError):
            registry.get_required_base_model("TestNonModel")

    def test_has_class(self):
        """Test checking if class exists in registry."""
        registry = ClassRegistry()

        registry.register_class(str)

        assert registry.has_class("str") is True
        assert registry.has_class("NonExistent") is False

    def test_has_subclass(self):
        """Test checking if subclass exists in registry."""
        registry = ClassRegistry()

        # Create test classes
        class TestBase:
            pass

        class TestChild(TestBase):
            pass

        class TestUnrelated:
            pass

        registry.register_class(TestChild)
        registry.register_class(TestUnrelated)

        # Valid subclass
        assert registry.has_subclass("TestChild", TestBase) is True

        # Invalid subclass
        assert registry.has_subclass("TestUnrelated", TestBase) is False

        # Non-existing class
        assert registry.has_subclass("NonExistent", TestBase) is False

    def test_logging_setup(self, mocker: MockerFixture):
        """Test logger setup and usage."""
        registry = ClassRegistry()

        # Test that set_logger method works without errors
        custom_logger = mocker.MagicMock()
        registry.set_logger(custom_logger)

        # Test that logging works with custom logger
        registry.register_class(str)

        # Verify the custom logger was used
        custom_logger.debug.assert_called_with("Registered new single class 'str' in registry")

    def test_logging_with_spy(self, mocker: MockerFixture):
        """Test logging functionality using spy to verify internal _log calls."""
        registry = ClassRegistry()

        # Spy on the internal _log method to verify it's called
        spy_log = mocker.spy(registry, "_log")

        registry.register_class(str)

        # Verify _log was called with correct message
        spy_log.assert_called_with("Registered new single class 'str' in registry")
