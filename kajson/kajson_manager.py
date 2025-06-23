from typing import ClassVar, Optional

from typing_extensions import Self

from kajson.class_registry import ClassRegistry
from kajson.class_registry_abstract import ClassRegistryAbstract

KAJSON_LOGGER_CHANNEL_NAME = "kajson.decoder"


class KajsonManager:
    _instance: ClassVar[Optional[Self]] = None

    @classmethod
    def get_instance(cls) -> Self:
        if cls._instance is None:
            raise RuntimeError("KajsonManager is not initialized")
        return cls._instance

    def __init__(self, logger_channel_name: Optional[str] = None, class_registry: Optional[ClassRegistryAbstract] = None) -> None:
        if self.__class__._instance is not None:
            raise RuntimeError("KajsonManager is already initialized")
        self.logger_channel_name = logger_channel_name or KAJSON_LOGGER_CHANNEL_NAME
        self._class_registry = class_registry or ClassRegistry()
        self.__class__._instance = self

    @classmethod
    def teardown(cls) -> None:
        cls._instance = None

    @classmethod
    def get_class_registry(cls) -> ClassRegistryAbstract:
        return cls.get_instance()._class_registry
