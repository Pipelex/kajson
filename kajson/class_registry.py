# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr, RootModel
from typing_extensions import override

from kajson.class_registry_abstract import ClassRegistryAbstract
from kajson.exceptions import ClassRegistryInheritanceError, ClassRegistryNotFoundError

LOGGING_LEVEL_VERBOSE = 5
CLASS_REGISTRY_LOGGER_CHANNEL_NAME = "class_registry"

ClassRegistryDict = Dict[str, Type[Any]]


class ClassRegistry(RootModel[ClassRegistryDict], ClassRegistryAbstract):
    root: ClassRegistryDict = Field(default_factory=dict)
    _logger: logging.Logger = PrivateAttr(default_factory=lambda: logging.getLogger(CLASS_REGISTRY_LOGGER_CHANNEL_NAME))

    def _log(self, message: str) -> None:
        self._logger.debug(message)

    def set_logger(self, logger: logging.Logger) -> None:
        self._logger = logger

    #########################################################################################
    # ClassProviderProtocol methods
    #########################################################################################

    @override
    def setup(self) -> None:
        pass

    @override
    def teardown(self) -> None:
        """Resets the registry to an empty state."""
        self.root = {}

    @override
    def register_class(
        self,
        class_type: Type[Any],
        name: Optional[str] = None,
        should_warn_if_already_registered: bool = True,
    ) -> None:
        """Registers a class in the registry with a name."""
        key = name or class_type.__name__
        if key in self.root:
            if should_warn_if_already_registered:
                self._log(f"Class '{name}' already exists in registry")
        else:
            self._log(f"Registered new single class '{key}' in registry")
        self.root[key] = class_type

    @override
    def unregister_class(self, class_type: Type[Any]) -> None:
        """Unregisters a class from the registry."""
        key = class_type.__name__
        if key not in self.root:
            raise ClassRegistryNotFoundError(f"Class '{key}' not found in registry")
        del self.root[key]
        self._log(f"Unregistered single class '{key}' from registry")

    @override
    def unregister_class_by_name(self, name: str) -> None:
        """Unregisters a class from the registry by its name."""
        if name not in self.root:
            raise ClassRegistryNotFoundError(f"Class '{name}' not found in registry")
        del self.root[name]

    @override
    def register_classes_dict(self, classes: Dict[str, Type[Any]]) -> None:
        """Registers multiple classes in the registry with names."""
        self.root.update(classes)
        nb_classes = len(classes)
        if nb_classes > 1:
            self._log(f"Registered {len(classes)} classes in registry")
            classes_list_str = "\n".join([f"{key}: {value.__name__}" for key, value in classes.items()])
            logging.log(level=LOGGING_LEVEL_VERBOSE, msg=classes_list_str)
        else:
            self._log(f"Registered single class '{list(classes.values())[0].__name__}' in registry")

    @override
    def register_classes(self, classes: List[Type[Any]]) -> None:
        """Registers multiple classes in the registry with names."""
        if not classes:
            self._log("register_classes called with empty list of classes to register")
            return

        for class_type in classes:
            key = class_type.__name__
            if key in self.root:
                self._log(f"Class '{key}' already exists in registry, skipping")
                continue
            self.root[key] = class_type
        nb_classes = len(classes)
        if nb_classes > 1:
            self._log(f"Registered {nb_classes} classes in registry")
            classes_list_str = "\n".join([f"{the_class.__name__}: {the_class}" for the_class in classes])
            logging.log(level=LOGGING_LEVEL_VERBOSE, msg=classes_list_str)
        else:
            self._log(f"Registered single class '{classes[0].__name__}' in registry")

    @override
    def get_class(self, name: str) -> Optional[Type[Any]]:
        """Retrieves a class from the registry by its name. Returns None if not found."""
        # First try exact match
        if name in self.root:
            return self.root[name]

        # If not found and name contains type parameters (generic type), strip them and try again
        if "[" in name and name.endswith("]"):
            base_name = name[: name.index("[")]
            self._log(f"Generic type '{name}' not found, trying base class '{base_name}'")
            return self.root.get(base_name)

        return None

    @override
    def get_required_class(self, name: str) -> Type[Any]:
        """Retrieves a class from the registry by its name. Raises an error if not found."""
        if name not in self.root:
            raise ClassRegistryNotFoundError(f"Class '{name}' not found in registry")
        return self.root[name]

    @override
    def get_required_subclass(self, name: str, base_class: Type[Any]) -> Type[Any]:
        """Retrieves a class from the registry by its name. Raises an error if not found."""
        if name not in self.root:
            raise ClassRegistryNotFoundError(f"Class '{name}' not found in registry")
        if not issubclass(self.root[name], base_class):
            raise ClassRegistryInheritanceError(f"Class '{name}' is not a subclass of {base_class}")
        return self.root[name]

    @override
    def get_required_base_model(self, name: str) -> Type[BaseModel]:
        return self.get_required_subclass(name=name, base_class=BaseModel)

    @override
    def has_class(self, name: str) -> bool:
        """Checks if a class is in the registry by its name."""
        return name in self.root

    @override
    def has_subclass(self, name: str, base_class: Type[Any]) -> bool:
        """Checks if a class is in the registry by its name."""
        if name not in self.root:
            return False
        if not issubclass(self.root[name], base_class):
            return False
        return True
