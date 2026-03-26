# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import BaseModel

from kajson.class_registry import ClassRegistry
from kajson.composite_class_registry import CompositeClassRegistry
from kajson.exceptions import ClassRegistryNotFoundError
from kajson.kajson_manager import KajsonManager


class ParentModel(BaseModel):
    value: str


class LocalModel(BaseModel):
    count: int


class OverrideModel(BaseModel):
    """Shares a name with ParentModel when registered under the same key."""

    override_value: str


class TestCompositeClassRegistry:
    def test_local_lookup_takes_priority(self) -> None:
        """When the same name exists in both local and parent, local wins."""
        parent = ClassRegistry()
        parent.register_class(ParentModel, name="Shared")
        composite = CompositeClassRegistry(parent=parent)
        composite.register_class(OverrideModel, name="Shared")

        result = composite.get_class(name="Shared")
        assert result is OverrideModel

    def test_fallback_to_parent(self) -> None:
        """When a name exists only in parent, composite finds it via fallback."""
        parent = ClassRegistry()
        parent.register_class(ParentModel)
        composite = CompositeClassRegistry(parent=parent)

        result = composite.get_class(name="ParentModel")
        assert result is ParentModel

    def test_registration_goes_to_local_only(self) -> None:
        """Registering via composite stores in local, not in parent."""
        parent = ClassRegistry()
        composite = CompositeClassRegistry(parent=parent)
        composite.register_class(LocalModel)

        assert composite.has_class(name="LocalModel")
        assert not parent.has_class(name="LocalModel")

    def test_teardown_clears_local_only(self) -> None:
        """Teardown clears local registry but leaves parent untouched."""
        parent = ClassRegistry()
        parent.register_class(ParentModel)
        composite = CompositeClassRegistry(parent=parent)
        composite.register_class(LocalModel)

        composite.teardown()

        assert not composite._local.has_class(name="LocalModel")
        assert parent.has_class(name="ParentModel")
        # Parent classes still accessible via composite
        assert composite.has_class(name="ParentModel")

    def test_has_class_checks_both(self) -> None:
        """has_class returns True for names in either local or parent."""
        parent = ClassRegistry()
        parent.register_class(ParentModel)
        composite = CompositeClassRegistry(parent=parent)
        composite.register_class(LocalModel)

        assert composite.has_class(name="ParentModel")
        assert composite.has_class(name="LocalModel")
        assert not composite.has_class(name="NonExistent")

    def test_unregister_from_local_only(self) -> None:
        """Unregistering removes from local only, parent is unaffected."""
        parent = ClassRegistry()
        parent.register_class(ParentModel)
        composite = CompositeClassRegistry(parent=parent)
        composite.register_class(LocalModel)

        composite.unregister_class(LocalModel)
        assert not composite._local.has_class(name="LocalModel")
        assert parent.has_class(name="ParentModel")

    def test_get_required_base_model_delegation(self) -> None:
        """get_required_base_model checks local first, then parent."""
        parent = ClassRegistry()
        parent.register_class(ParentModel)
        composite = CompositeClassRegistry(parent=parent)
        composite.register_class(LocalModel)

        # Local model found
        result = composite.get_required_base_model(name="LocalModel")
        assert result is LocalModel

        # Parent model found via fallback
        result = composite.get_required_base_model(name="ParentModel")
        assert result is ParentModel

    def test_get_required_class_raises_when_missing(self) -> None:
        """get_required_class raises when name is in neither local nor parent."""
        parent = ClassRegistry()
        composite = CompositeClassRegistry(parent=parent)

        with pytest.raises(ClassRegistryNotFoundError):
            composite.get_required_class(name="NonExistent")

    def test_scoped_context_var(self) -> None:
        """Setting scoped registry makes get_class_registry() return it; unsetting restores global."""
        global_registry = KajsonManager.get_class_registry()
        parent = ClassRegistry()
        scoped = CompositeClassRegistry(parent=parent)

        KajsonManager.set_scoped_class_registry(scoped)
        try:
            assert KajsonManager.get_class_registry() is scoped
        finally:
            KajsonManager.set_scoped_class_registry(None)

        assert KajsonManager.get_class_registry() is global_registry
