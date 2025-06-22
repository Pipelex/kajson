# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

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
        class_type: Type[Any],
        name: Optional[str] = None,
        should_warn_if_already_registered: bool = True,
    ) -> None:
        pass

    @abstractmethod
    def unregister_class(self, class_type: Type[Any]) -> None:
        pass

    @abstractmethod
    def unregister_class_by_name(self, name: str) -> None:
        pass

    @abstractmethod
    def register_classes_dict(self, classes: Dict[str, Type[Any]]) -> None:
        pass

    @abstractmethod
    def register_classes(self, classes: List[Type[Any]]) -> None:
        pass

    @abstractmethod
    def get_class(self, name: str) -> Optional[Type[Any]]:
        pass

    @abstractmethod
    def get_required_class(self, name: str) -> Type[Any]:
        pass

    @abstractmethod
    def get_required_subclass(self, name: str, base_class: Type[Any]) -> Type[Any]:
        pass

    @abstractmethod
    def get_required_base_model(self, name: str) -> Type[BaseModel]:
        pass

    @abstractmethod
    def has_class(self, name: str) -> bool:
        pass

    @abstractmethod
    def has_subclass(self, name: str, base_class: Type[Any]) -> bool:
        pass
