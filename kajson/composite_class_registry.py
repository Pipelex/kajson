# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel
from typing_extensions import override

from kajson.class_registry import ClassRegistry
from kajson.class_registry_abstract import ClassRegistryAbstract
from kajson.exceptions import ClassRegistryInheritanceError


class CompositeClassRegistry(ClassRegistryAbstract):
    """A ClassRegistry that layers a local registry on top of a parent (global) registry.

    Lookups check local first, then fall back to parent.
    Registrations and mutations only affect the local layer.
    Teardown clears the local layer without touching the parent.
    """

    def __init__(self, parent: ClassRegistryAbstract) -> None:
        self._parent = parent
        self._local = ClassRegistry()

    @override
    def setup(self) -> None:
        pass

    @override
    def teardown(self) -> None:
        self._local.teardown()

    @override
    def register_class(
        self,
        class_type: Type[Any],
        name: Optional[str] = None,
        should_warn_if_already_registered: bool = True,
    ) -> None:
        self._local.register_class(
            class_type=class_type,
            name=name,
            should_warn_if_already_registered=should_warn_if_already_registered,
        )

    @override
    def unregister_class(self, class_type: Type[Any]) -> None:
        self._local.unregister_class(class_type=class_type)

    @override
    def unregister_class_by_name(self, name: str) -> None:
        self._local.unregister_class_by_name(name=name)

    @override
    def register_classes_dict(self, classes: Dict[str, Type[Any]]) -> None:
        self._local.register_classes_dict(classes=classes)

    @override
    def register_classes(self, classes: List[Type[Any]]) -> None:
        self._local.register_classes(classes=classes)

    @override
    def get_class(self, name: str) -> Optional[Type[Any]]:
        local_result = self._local.get_class(name=name)
        if local_result is not None:
            return local_result
        return self._parent.get_class(name=name)

    @override
    def get_required_class(self, name: str) -> Type[Any]:
        local_result = self._local.get_class(name=name)
        if local_result is not None:
            return local_result
        return self._parent.get_required_class(name=name)

    @override
    def get_required_subclass(self, name: str, base_class: Type[Any]) -> Type[Any]:
        local_result = self._local.get_class(name=name)
        if local_result is not None:
            if not issubclass(local_result, base_class):
                msg = f"Class '{name}' is not a subclass of {base_class}"
                raise ClassRegistryInheritanceError(msg)
            return local_result
        return self._parent.get_required_subclass(name=name, base_class=base_class)

    @override
    def get_required_base_model(self, name: str) -> Type[BaseModel]:
        return self.get_required_subclass(name=name, base_class=BaseModel)

    @override
    def has_class(self, name: str) -> bool:
        return self._local.has_class(name=name) or self._parent.has_class(name=name)

    @override
    def has_subclass(self, name: str, base_class: Type[Any]) -> bool:
        if self._local.has_subclass(name=name, base_class=base_class):
            return True
        return self._parent.has_subclass(name=name, base_class=base_class)
