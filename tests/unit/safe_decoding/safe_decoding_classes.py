# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""Classes that the safe-decoding tests' payloads name.

They live at module level so that a marker naming this module resolves them from sys.modules, as a
real payload would. The counting classes record every call to the construction step a payload must
not reach, so a refusal test can prove that nothing ran.
"""

import dataclasses
import json
import uuid
from enum import Enum, EnumMeta
from pathlib import Path
from typing import Any, ClassVar, Dict, Generic, List, TypeVar

import pydantic_settings
from pydantic import BaseModel, RootModel, field_validator
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.dataclasses import dataclass as pydantic_dataclass
from typing_extensions import override

from kajson.json_decoder import UniversalJSONDecoder

ValueType = TypeVar("ValueType")

MODULE_NAME = __name__


def make_marker(class_name: str, module_name: str = MODULE_NAME, **fields: Any) -> str:
    """Write a JSON object carrying a class marker and the given fields."""
    return json.dumps({"__class__": class_name, "__module__": module_name, **fields})


def error_chain_text(exc: BaseException) -> str:
    """Concatenate the text of an exception and of every exception chained to it."""
    texts: List[str] = []
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        texts.append(str(current))
        texts.append(repr(current))
        current = current.__cause__ or current.__context__
    return "\n".join(texts)


class KeywordConstructorCounter:
    calls: ClassVar[int] = 0

    def __init__(self, **kwargs: Any) -> None:
        KeywordConstructorCounter.calls += 1


class NoArgConstructorCounter:
    calls: ClassVar[int] = 0

    def __init__(self) -> None:
        NoArgConstructorCounter.calls += 1


@dataclasses.dataclass
class StdlibDataclass:
    number: int


class PlainModel(BaseModel):
    name: str
    count: int = 0


class AnyFieldModel(BaseModel):
    payload: Any


class Box(BaseModel, Generic[ValueType]):
    value: ValueType


class IntListRoot(RootModel[List[int]]):
    pass


@pydantic_dataclass
class PydanticPoint:
    abscissa: int
    ordinate: int


class Color(Enum):
    RED = "red"
    GREEN = "green"


class WithJsonDecode:
    def __init__(self, value: int) -> None:
        self.value = value

    def __json_encode__(self) -> Dict[str, Any]:
        return {"value": self.value}

    @staticmethod
    def __json_decode__(the_dict: Dict[str, Any]) -> "WithJsonDecode":
        return WithJsonDecode(the_dict["value"])


class WithFailingJsonDecode:
    @staticmethod
    def __json_decode__(the_dict: Dict[str, Any]) -> "WithFailingJsonDecode":
        msg = "hook failed"
        raise ValueError(msg)


class WithAttributeErrorJsonDecode:
    @staticmethod
    def __json_decode__(the_dict: Dict[str, Any]) -> "WithAttributeErrorJsonDecode":
        msg = "hook failed with an AttributeError"
        raise AttributeError(msg)


class WithRegisteredDecoder:
    def __init__(self, value: int) -> None:
        self.value = value


class WithFailingRegisteredDecoder:
    pass


def decode_with_registered(the_dict: Dict[str, Any]) -> WithRegisteredDecoder:
    return WithRegisteredDecoder(the_dict["value"])


def failing_registered_decoder(the_dict: Dict[str, Any]) -> WithFailingRegisteredDecoder:
    msg = "registered decoder failed"
    raise ValueError(msg)


class InitOverridingModel(BaseModel):
    calls: ClassVar[int] = 0
    number: int = 0

    def __init__(self, **data: Any) -> None:
        InitOverridingModel.calls += 1
        super().__init__(**data)


class BaseInitFlaggedModel(BaseModel):
    """`model_validate` skips an `__init__` flagged `__pydantic_base_init__`; only a constructor call would run it."""

    calls: ClassVar[int] = 0
    number: int = 0

    def __init__(self, **data: Any) -> None:
        BaseInitFlaggedModel.calls += 1
        super().__init__(**data)

    __init__.__pydantic_base_init__ = True  # type: ignore[attr-defined]  # pyright: ignore[reportFunctionMemberAccess]


class NewOverridingModel(BaseModel):
    calls: ClassVar[int] = 0
    number: int = 0

    def __new__(cls, *args: Any, **kwargs: Any) -> "NewOverridingModel":
        NewOverridingModel.calls += 1
        return super().__new__(cls)


class CountingModelMetaclass(ModelMetaclass):
    calls: ClassVar[int] = 0

    @override
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        CountingModelMetaclass.calls += 1
        return super().__call__(*args, **kwargs)


class MetaclassCallModel(BaseModel, metaclass=CountingModelMetaclass):
    number: int = 0


class InitOverridingRoot(RootModel[int]):
    calls: ClassVar[int] = 0

    def __init__(self, root: int = 0) -> None:
        InitOverridingRoot.calls += 1
        super().__init__(root)  # pyright: ignore[reportUnknownMemberType]


class CountingEnumMeta(EnumMeta):
    calls: ClassVar[int] = 0

    @override
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:  # pyright: ignore[reportIncompatibleMethodOverride]
        CountingEnumMeta.calls += 1
        return super().__call__(*args, **kwargs)  # pyright: ignore[reportUnknownVariableType]


class MetaclassCallEnum(Enum, metaclass=CountingEnumMeta):
    ONE = 1


class ValidatedModel(BaseModel):
    value: int

    @field_validator("value")
    @classmethod
    def must_be_positive(cls, value: int) -> int:
        if value <= 0:
            msg = "value must be positive"
            raise ValueError(msg)
        return value


class EnvFileSettings(pydantic_settings.BaseSettings):
    sentinel_token: str = ""


COUNTED_CLASSES = (
    KeywordConstructorCounter,
    NoArgConstructorCounter,
    InitOverridingModel,
    BaseInitFlaggedModel,
    NewOverridingModel,
    CountingModelMetaclass,
    InitOverridingRoot,
    CountingEnumMeta,
)


class ResolvingSubclass(UniversalJSONDecoder):
    """Stands for pipelex-server's RestrictedPayloadDecoder: replaces resolution, keeps kajson's rebuild."""

    @override
    def universal_decoder(self, the_dict: Dict[str, Any]) -> Any:
        if "__class__" not in the_dict:
            return the_dict
        class_name = the_dict.pop("__class__")
        the_dict.pop("__module__")
        assert self._class_registry is not None
        the_class = self._class_registry.get_class(name=class_name)
        assert the_class is not None
        return self._apply_decoder_strategies(the_class, class_name, the_dict)


_PROBE_MODULE_SOURCE = """\
import pathlib
pathlib.Path({record!r}).joinpath({module!r}).write_text("imported")
from pydantic import BaseModel


class ProbeModel(BaseModel):
    value: int
"""


class ProbePackages:
    """Probe packages under a unique prefix that record their own import in a directory.

    Module names are given relative to the prefix: '' is the prefix package itself, 'sub.leaf' is
    '<prefix>.sub.leaf', and 'evil' is the sibling top-level package '<prefix>evil'.
    """

    def __init__(self, root: Path, record_dir: Path) -> None:
        self.prefix = f"kjprobe_{uuid.uuid4().hex[:12]}"
        self.root = root
        self.record_dir = record_dir

    def write(self, module: str) -> None:
        full_name = self.full(module)
        package_dir = self.root.joinpath(*full_name.split("."))
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text(_PROBE_MODULE_SOURCE.format(record=str(self.record_dir), module=full_name))

    def full(self, module: str) -> str:
        if module.startswith("evil"):
            return self.prefix + module
        if module:
            return f"{self.prefix}.{module}"
        return self.prefix

    def was_imported(self, module: str) -> bool:
        return (self.record_dir / self.full(module)).exists()
