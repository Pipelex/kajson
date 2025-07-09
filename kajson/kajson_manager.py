from typing import Optional

from typing_extensions import Self

from kajson.class_registry import ClassRegistry
from kajson.class_registry_abstract import ClassRegistryAbstract
from kajson.singleton import MetaSingleton

KAJSON_LOGGER_CHANNEL_NAME = "kajson"


class KajsonManager(metaclass=MetaSingleton):
    """A singleton class for managing kajson operations."""

    def __init__(self, logger_channel_name: Optional[str] = None, class_registry: Optional[ClassRegistryAbstract] = None) -> None:
        self.logger_channel_name = logger_channel_name or KAJSON_LOGGER_CHANNEL_NAME
        self._class_registry = class_registry or ClassRegistry()

    @classmethod
    def get_instance(cls) -> Self:
        """Get the singleton instance. This will create one if it doesn't exist."""
        return cls()

    @classmethod
    def teardown(cls) -> None:
        """Destroy the singleton instance."""
        if cls in MetaSingleton.instances:
            del MetaSingleton.instances[cls]

    @classmethod
    def get_class_registry(cls) -> ClassRegistryAbstract:
        return cls.get_instance()._class_registry
