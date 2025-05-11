# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr, RootModel

from kajson.exceptions import ClassRegistryInheritanceError, ClassRegistryNotFoundError
from kajson.module_utils import find_classes_in_module, import_module_from_file
from kajson.sandbox_manager import sandbox_manager

LOGGING_LEVEL_VERBOSE = 5
CLASS_REGISTRY_LOGGER_CHANNEL_NAME = "class_registry"
CLASS_REGISTRY_LOGGER_CHANNEL_NAME_IN_SANDBOX = "class_registry.sandbox"

ClassRegistryDict = Dict[str, Type[Any]]


def find_files_in_dir(dir_path: str, pattern: str, is_recursive: bool) -> List[Path]:
    """
    Find files matching a pattern in a directory.

    Args:
        dir_path: Directory path to search in
        pattern: File pattern to match (e.g. "*.py")
        recursive: Whether to search recursively in subdirectories

    Returns:
        List of matching Path objects
    """
    path = Path(dir_path)
    if is_recursive:
        return list(path.rglob(pattern))
    else:
        return list(path.glob(pattern))


class ClassRegistry(RootModel[ClassRegistryDict]):
    root: ClassRegistryDict = Field(default_factory=dict)
    _logger: logging.Logger = PrivateAttr(logging.getLogger(CLASS_REGISTRY_LOGGER_CHANNEL_NAME))

    def log(self, message: str) -> None:
        if sandbox_manager.is_in_sandbox():
            logger = logging.getLogger(CLASS_REGISTRY_LOGGER_CHANNEL_NAME_IN_SANDBOX)
            logger.debug(message)
        else:
            self._logger.debug(message)

    def reset(self) -> None:
        """Resets the registry to an empty state."""
        self.root = {}

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
                self.log(f"Class '{name}' already exists in registry")
        else:
            self.log(f"Registered new single class '{key}' in registry")
        self.root[key] = class_type

    def unregister_class(self, class_type: Type[Any]) -> None:
        """Unregisters a class from the registry."""
        key = class_type.__name__
        if key not in self.root:
            raise ClassRegistryNotFoundError(f"Class '{key}' not found in registry")
        del self.root[key]
        self.log(f"Unregistered single class '{key}' from registry")

    def unregister_class_by_name(self, name: str) -> None:
        """Unregisters a class from the registry by its name."""
        if name not in self.root:
            raise ClassRegistryNotFoundError(f"Class '{name}' not found in registry")
        del self.root[name]

    def register_classes_dict(self, classes: Dict[str, Type[Any]]) -> None:
        """Registers multiple classes in the registry with names."""
        self.root.update(classes)
        nb_classes = len(classes)
        if nb_classes > 1:
            self.log(f"Registered {len(classes)} classes in registry")
            classes_list_str = "\n".join([f"{key}: {value.__name__}" for key, value in classes.items()])
            logging.log(level=LOGGING_LEVEL_VERBOSE, msg=classes_list_str)
        else:
            self.log(f"Registered single class '{list(classes.values())[0].__name__}' in registry")

    def register_classes(self, classes: List[Type[Any]]) -> None:
        """Registers multiple classes in the registry with names."""
        if not classes:
            self.log("register_classes called with empty list of classes to register")
            return

        for class_type in classes:
            key = class_type.__name__
            if key in self.root:
                self.log(f"Class '{key}' already exists in registry, skipping")
                continue
            self.root[key] = class_type
        nb_classes = len(classes)
        if nb_classes > 1:
            self.log(f"Registered {nb_classes} classes in registry")
            classes_list_str = "\n".join([f"{the_class.__name__}: {the_class}" for the_class in classes])
            logging.log(level=LOGGING_LEVEL_VERBOSE, msg=classes_list_str)
        else:
            self.log(f"Registered single class '{classes[0].__name__}' in registry")

    def get_class(self, name: str) -> Optional[Type[Any]]:
        """Retrieves a class from the registry by its name. Returns None if not found."""
        return self.root.get(name)

    def get_required_class(self, name: str) -> Type[Any]:
        """Retrieves a class from the registry by its name. Raises an error if not found."""
        if name not in self.root:
            raise ClassRegistryNotFoundError(f"Class '{name}' not found in registry")
        return self.root[name]

    def get_required_subclass(self, name: str, base_class: Type[Any]) -> Type[Any]:
        """Retrieves a class from the registry by its name. Raises an error if not found."""
        if name not in self.root:
            raise ClassRegistryNotFoundError(f"Class '{name}' not found in registry")
        if not issubclass(self.root[name], base_class):
            raise ClassRegistryInheritanceError(f"Class '{name}' is not a subclass of {base_class}")
        return self.root[name]

    def get_required_base_model(self, name: str) -> Type[BaseModel]:
        return self.get_required_subclass(name=name, base_class=BaseModel)

    def has_class(self, name: str) -> bool:
        """Checks if a class is in the registry by its name."""
        return name in self.root

    def has_subclass(self, name: str, base_class: Type[Any]) -> bool:
        """Checks if a class is in the registry by its name."""
        if name not in self.root:
            return False
        if not issubclass(self.root[name], base_class):
            return False
        return True

    def register_classes_in_file(
        self,
        file_path: str,
        base_class: Optional[Type[Any]],
        is_include_imported: bool,
    ) -> None:
        """Processes a Python file to find and register classes."""
        module = import_module_from_file(file_path)

        # Find classes that match criteria
        classes_to_register = find_classes_in_module(
            module=module,
            base_class=base_class,
            include_imported=is_include_imported,
        )

        # Clean up sys.modules to prevent memory leaks
        del sys.modules[module.__name__]

        self.register_classes(classes=classes_to_register)

    def register_classes_in_folder(
        self,
        folder_path: str,
        base_class: Optional[Type[Any]] = None,
        is_recursive: bool = True,
        is_include_imported: bool = False,
    ) -> None:
        """
        Registers all classes in Python files within folders that are subclasses of base_class.
        If base_class is None, registers all classes.

        Args:
            folder_paths: List of paths to folders containing Python files
            base_class: Optional base class to filter registerable classes
            recursive: Whether to search recursively in subdirectories
            exclude_files: List of filenames to exclude
            exclude_dirs: List of directory names to exclude
            include_imported: Whether to include classes imported from other modules
        """

        python_files = find_files_in_dir(
            dir_path=folder_path,
            pattern="*.py",
            is_recursive=is_recursive,
        )

        for python_file in python_files:
            self.register_classes_in_file(
                file_path=str(python_file),
                base_class=base_class,
                is_include_imported=is_include_imported,
            )


class_registry = ClassRegistry()
