from typing import Any, ClassVar, Dict, Type

from typing_extensions import override


class MetaSingleton(type):
    """Simple implementation of a singleton using a metaclass."""

    instances: ClassVar[Dict[Type[Any], Any]] = {}

    @override
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls.instances:  # pyright: ignore[reportUnnecessaryContains]
            cls.instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls.instances[cls]
