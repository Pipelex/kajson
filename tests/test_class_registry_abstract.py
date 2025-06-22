# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import inspect
from abc import ABC
from typing import Any, Dict, List, Optional, Type

import pytest
from pydantic import BaseModel
from typing_extensions import override

from kajson.class_registry import ClassRegistry
from kajson.class_registry_abstract import ClassRegistryAbstract


class TestClassRegistryAbstract:
    """Test suite for ClassRegistryAbstract to verify its abstract behavior."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that ClassRegistryAbstract cannot be instantiated directly."""
        with pytest.raises(TypeError) as excinfo:
            ClassRegistryAbstract()  # type: ignore[abstract]

        assert "Can't instantiate abstract class" in str(excinfo.value)
        assert "ClassRegistryAbstract" in str(excinfo.value)

    def test_is_abstract_base_class(self):
        """Test that ClassRegistryAbstract is properly defined as an ABC."""
        assert issubclass(ClassRegistryAbstract, ABC)
        assert inspect.isabstract(ClassRegistryAbstract)

    def test_all_methods_are_abstract(self):
        """Test that all expected methods are defined as abstract methods."""
        abstract_methods = ClassRegistryAbstract.__abstractmethods__

        expected_methods = {
            "setup",
            "teardown",
            "register_class",
            "unregister_class",
            "unregister_class_by_name",
            "register_classes_dict",
            "register_classes",
            "get_class",
            "get_required_class",
            "get_required_subclass",
            "get_required_base_model",
            "has_class",
            "has_subclass",
        }

        assert abstract_methods == expected_methods

    def test_method_signatures(self):
        """Test that abstract methods have the correct signatures."""
        # Test setup method
        setup_method = getattr(ClassRegistryAbstract, "setup")
        setup_sig = inspect.signature(setup_method)
        assert list(setup_sig.parameters.keys()) == ["self"]
        assert setup_sig.return_annotation is None

        # Test teardown method
        teardown_method = getattr(ClassRegistryAbstract, "teardown")
        teardown_sig = inspect.signature(teardown_method)
        assert list(teardown_sig.parameters.keys()) == ["self"]
        assert teardown_sig.return_annotation is None

        # Test register_class method
        register_class_method = getattr(ClassRegistryAbstract, "register_class")
        register_class_sig = inspect.signature(register_class_method)
        params = register_class_sig.parameters
        assert "self" in params
        assert "class_type" in params
        assert "name" in params
        assert "should_warn_if_already_registered" in params
        assert params["name"].default is None
        assert params["should_warn_if_already_registered"].default is True
        assert register_class_sig.return_annotation is None

        # Test get_class method
        get_class_method = getattr(ClassRegistryAbstract, "get_class")
        get_class_sig = inspect.signature(get_class_method)
        params = get_class_sig.parameters
        assert "self" in params
        assert "name" in params
        assert get_class_sig.return_annotation == Optional[Type[Any]]

        # Test register_classes_in_folder method
        # register_folder_method = getattr(ClassRegistryAbstract, "register_classes_in_folder")
        # register_folder_sig = inspect.signature(register_folder_method)
        # params = register_folder_sig.parameters
        # assert "self" in params
        # assert "folder_path" in params
        # assert "base_class" in params
        # assert "is_recursive" in params
        # assert "is_include_imported" in params
        # assert params["base_class"].default is None
        # assert params["is_recursive"].default is True
        # assert params["is_include_imported"].default is False

    def test_incomplete_subclass_cannot_be_instantiated(self):
        """Test that subclasses missing abstract method implementations cannot be instantiated."""

        class IncompleteRegistry(ClassRegistryAbstract):
            """Incomplete implementation missing most abstract methods."""

            @override
            def setup(self) -> None:
                pass

            @override
            def teardown(self) -> None:
                pass

            # Missing all other abstract methods

        with pytest.raises(TypeError) as excinfo:
            IncompleteRegistry()  # type: ignore[abstract]

        assert "Can't instantiate abstract class" in str(excinfo.value)
        assert "IncompleteRegistry" in str(excinfo.value)

    def test_complete_subclass_can_be_instantiated(self):
        """Test that a complete subclass implementation can be instantiated."""

        class CompleteRegistry(ClassRegistryAbstract):
            """Complete implementation of all abstract methods."""

            @override
            def setup(self) -> None:
                pass

            @override
            def teardown(self) -> None:
                pass

            @override
            def register_class(
                self,
                class_type: Type[Any],
                name: Optional[str] = None,
                should_warn_if_already_registered: bool = True,
            ) -> None:
                pass

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
                return None

            @override
            def get_required_class(self, name: str) -> Type[Any]:
                return str

            @override
            def get_required_subclass(self, name: str, base_class: Type[Any]) -> Type[Any]:
                return str

            @override
            def get_required_base_model(self, name: str) -> Type[BaseModel]:
                class DummyModel(BaseModel):
                    pass

                return DummyModel

            @override
            def has_class(self, name: str) -> bool:
                return False

            @override
            def has_subclass(self, name: str, base_class: Type[Any]) -> bool:
                return False

        # Should not raise an exception
        registry = CompleteRegistry()
        assert isinstance(registry, ClassRegistryAbstract)
        assert isinstance(registry, CompleteRegistry)

    def test_partial_implementation_fails(self):
        """Test various partial implementations to ensure they fail appropriately."""

        # Missing setup and teardown
        class MissingSetupTeardown(ClassRegistryAbstract):
            @override
            def register_class(self, class_type: Type[Any], name: Optional[str] = None, should_warn_if_already_registered: bool = True) -> None:
                pass

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
                return None

            @override
            def get_required_class(self, name: str) -> Type[Any]:
                return str

            @override
            def get_required_subclass(self, name: str, base_class: Type[Any]) -> Type[Any]:
                return str

            @override
            def get_required_base_model(self, name: str) -> Type[BaseModel]:
                class DummyModel(BaseModel):
                    pass

                return DummyModel

            @override
            def has_class(self, name: str) -> bool:
                return False

            @override
            def has_subclass(self, name: str, base_class: Type[Any]) -> bool:
                return False

        with pytest.raises(TypeError):
            MissingSetupTeardown()  # type: ignore[abstract]

        # Missing registration methods
        class MissingRegistrationMethods(ClassRegistryAbstract):
            @override
            def setup(self) -> None:
                pass

            @override
            def teardown(self) -> None:
                pass

            @override
            def get_class(self, name: str) -> Optional[Type[Any]]:
                return None

            @override
            def get_required_class(self, name: str) -> Type[Any]:
                return str

            @override
            def get_required_subclass(self, name: str, base_class: Type[Any]) -> Type[Any]:
                return str

            @override
            def get_required_base_model(self, name: str) -> Type[BaseModel]:
                class DummyModel(BaseModel):
                    pass

                return DummyModel

            @override
            def has_class(self, name: str) -> bool:
                return False

            @override
            def has_subclass(self, name: str, base_class: Type[Any]) -> bool:
                return False

        with pytest.raises(TypeError):
            MissingRegistrationMethods()  # type: ignore[abstract]

    def test_method_documentation(self):
        """Test that abstract methods can have docstrings (though none are present in this case)."""
        # This test verifies the structure allows for documentation
        # The actual abstract class doesn't have docstrings, which is fine
        for method_name in ClassRegistryAbstract.__abstractmethods__:
            method = getattr(ClassRegistryAbstract, method_name)
            assert callable(method)
            # We're just verifying the methods exist and are callable
            # Docstrings are optional for abstract methods

    def test_inheritance_chain(self):
        """Test the inheritance chain of ClassRegistryAbstract."""
        # Check MRO (Method Resolution Order)
        mro = ClassRegistryAbstract.__mro__
        assert len(mro) >= 2  # At least ClassRegistryAbstract and object
        assert mro[0] == ClassRegistryAbstract
        assert ABC in mro
        assert object in mro

    def test_type_annotations_present(self):
        """Test that type annotations are properly defined for abstract methods."""
        # Check method annotations via inspection
        for method_name in ["get_class", "get_required_class", "has_class", "has_subclass"]:
            method = getattr(ClassRegistryAbstract, method_name)
            sig = inspect.signature(method)
            assert sig.return_annotation is not inspect.Signature.empty

    def test_concrete_implementation_follows_abstract_interface(self):
        """Test that ClassRegistry properly implements the abstract interface."""
        # Verify ClassRegistry is a subclass of ClassRegistryAbstract
        assert issubclass(ClassRegistry, ClassRegistryAbstract)

        # Create instance to test interface compliance
        registry = ClassRegistry()
        assert isinstance(registry, ClassRegistryAbstract)

        # Test that all abstract methods are implemented
        for method_name in ClassRegistryAbstract.__abstractmethods__:
            assert hasattr(registry, method_name)
            method = getattr(registry, method_name)
            assert callable(method)

    def test_abstract_methods_via_concrete_implementation(self):
        """Test abstract method signatures through concrete implementation."""
        registry = ClassRegistry()

        # Test that we can call all abstract methods through concrete implementation
        # This exercises the abstract method signatures and helps with coverage

        # Test basic lifecycle methods
        registry.setup()  # Should not raise
        registry.teardown()  # Should not raise

        # Test registration methods
        registry.register_class(str, "String")
        registry.register_classes_dict({"Integer": int})
        registry.register_classes([float])

        # Test query methods
        assert registry.get_class("String") is str
        assert registry.get_required_class("String") is str
        assert registry.has_class("String") is True
        assert registry.has_subclass("String", object) is True

        # Test cleanup
        registry.unregister_class_by_name("String")
        registry.unregister_class_by_name("Integer")  # int was registered as "Integer"
        registry.unregister_class(float)  # float was registered with its default name

    def test_abstract_method_resolution_order(self):
        """Test that method resolution works correctly through inheritance."""
        registry = ClassRegistry()

        # Test that calling methods on the instance resolves to concrete implementations
        # This helps ensure the abstract methods are properly overridden

        # Get method objects directly from the class
        abstract_setup = ClassRegistryAbstract.setup
        concrete_setup = ClassRegistry.setup

        # Verify they are different methods (abstract vs concrete)
        assert abstract_setup is not concrete_setup

        # Verify the concrete implementation is used by checking the MRO
        assert hasattr(registry, "setup")
        # The bound method should be from the concrete class, not abstract
        registry_method = getattr(registry.__class__, "setup")
        assert registry_method is concrete_setup

    def test_abstract_class_method_signatures_match_concrete(self):
        """Test that concrete implementation maintains abstract method signatures."""
        for method_name in ClassRegistryAbstract.__abstractmethods__:
            abstract_method = getattr(ClassRegistryAbstract, method_name)
            concrete_method = getattr(ClassRegistry, method_name)

            abstract_sig = inspect.signature(abstract_method)
            concrete_sig = inspect.signature(concrete_method)

            # Parameter names should match (excluding 'self')
            abstract_params = list(abstract_sig.parameters.keys())[1:]  # Skip 'self'
            concrete_params = list(concrete_sig.parameters.keys())[1:]  # Skip 'self'

            assert abstract_params == concrete_params, f"Parameter mismatch in {method_name}"
