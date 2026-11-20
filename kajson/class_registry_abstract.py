# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class ClassRegistryAbstract(ABC):
    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def teardown(self) -> None:
        pass

    @abstractmethod
    def register_class(
        self,
        class_type: type[Any],
        name: Optional[str] = None,
        should_warn_if_already_registered: bool = True,
    ) -> None:
        pass

    @abstractmethod
    def unregister_class(self, class_type: type[Any]) -> None:
        pass

    @abstractmethod
    def unregister_class_by_name(self, name: str) -> None:
        pass

    @abstractmethod
    def register_classes_dict(self, classes: dict[str, type[Any]]) -> None:
        pass

    @abstractmethod
    def register_classes(self, classes: list[type[Any]]) -> None:
        pass

    @abstractmethod
    def get_class(self, name: str) -> Optional[type[Any]]:
        pass

    @abstractmethod
    def get_required_class(self, name: str) -> type[Any]:
        pass

    @abstractmethod
    def get_required_subclass(self, name: str, base_class: type[Any]) -> type[Any]:
        pass

    @abstractmethod
    def get_required_base_model(self, name: str) -> type[BaseModel]:
        pass

    @abstractmethod
    def has_class(self, name: str) -> bool:
        pass

    @abstractmethod
    def has_subclass(self, name: str, base_class: type[Any]) -> bool:
        pass

    @abstractmethod
    def get_classes_dict(self) -> dict[str, type[Any]]:
        """Returns a snapshot dict of all registered classes by name.

        The returned dict is a copy — mutating it does not affect the registry.
        Useful for pre-seeding a scoped registry from another one.
        """
        pass
