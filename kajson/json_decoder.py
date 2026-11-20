# SPDX-FileCopyrightText: © 2018 Bastien Pietropaoli
# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""
Copyright (c) 2018 Bastien Pietropaoli

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

All additions and modifications are Copyright (c) 2025 Evotis S.A.S.
"""

from __future__ import annotations

import importlib
import json
import logging
import sys
import warnings
from collections.abc import Callable, Iterable
from enum import Enum, EnumMeta
from typing import Any, ClassVar, TypeVar, cast

from pydantic import BaseModel, RootModel, ValidationError
from pydantic.dataclasses import is_pydantic_dataclass, rebuild_dataclass

from kajson.class_registry_abstract import ClassRegistryAbstract
from kajson.exceptions import KajsonDecoderError
from kajson.kajson_manager import KajsonManager

DECODER_LOGGER_CHANNEL_NAME = "kajson.decoder"
IS_DECODER_FALLBACK_ENABLED = False
FALLBACK_MESSAGE = " Trying something else."

# Longest payload-supplied name quoted in full in an error message; longer names are cut.
_MAX_QUOTED_NAME_LENGTH = 200

SAFE_MODE_REBUILDABLE_KINDS = (
    "a pydantic BaseModel or RootModel, a pydantic dataclass, an Enum, a class with a registered decoder, or a class with a __json_decode__ hook"
)


T = TypeVar("T")


class _DecodeStrategy(Enum):
    """The ways the decoder can rebuild an object from a resolved class and its dict."""

    REGISTERED_DECODER = "registered_decoder"
    JSON_DECODE_HOOK = "json_decode_hook"
    ROOT_MODEL = "root_model"
    ENUM = "enum"
    BASE_MODEL = "base_model"
    PYDANTIC_DATACLASS = "pydantic_dataclass"
    GENERIC_CONSTRUCTOR = "generic_constructor"

    @property
    def is_allowed_in_safe_mode(self) -> bool:
        """Whether safe mode may rebuild with this strategy: everything but calling the class with the payload's keys."""
        match self:
            case (
                _DecodeStrategy.REGISTERED_DECODER
                | _DecodeStrategy.JSON_DECODE_HOOK
                | _DecodeStrategy.ROOT_MODEL
                | _DecodeStrategy.ENUM
                | _DecodeStrategy.BASE_MODEL
                | _DecodeStrategy.PYDANTIC_DATACLASS
            ):
                return True
            case _DecodeStrategy.GENERIC_CONSTRUCTOR:
                return False

    @property
    def kind_label(self) -> str:
        """The kind of class the strategy rebuilds, for messages."""
        match self:
            case _DecodeStrategy.ENUM:
                return "enum"
            case _DecodeStrategy.ROOT_MODEL | _DecodeStrategy.BASE_MODEL | _DecodeStrategy.PYDANTIC_DATACLASS:
                return "pydantic class"
            case _DecodeStrategy.REGISTERED_DECODER | _DecodeStrategy.JSON_DECODE_HOOK | _DecodeStrategy.GENERIC_CONSTRUCTOR:
                return "class"


# The construction steps of the library classes safe mode compares against, by identity.
_BASE_MODEL_INIT: Any = BaseModel.__init__
_BASE_MODEL_VALIDATE_FUNC: Any = cast(Any, BaseModel.model_validate).__func__
_ROOT_MODEL_INIT: Any = cast(Any, RootModel).__init__
_ENUM_META_CALL: Any = EnumMeta.__call__
_ENUM_META_GETITEM: Any = EnumMeta.__getitem__


class _Declined:
    """Sentinel type: a strategy gave up and the permissive chain moves on to the next one."""


_DECLINED = _Declined()


class _Missing:
    """Sentinel type: a name is absent from a module."""


_MISSING = _Missing()


def _quote_name(name: str) -> str:
    """Quote a payload-supplied name for an error message, cutting an overly long one."""
    if len(name) > _MAX_QUOTED_NAME_LENGTH:
        return repr(name[:_MAX_QUOTED_NAME_LENGTH]) + "…"
    return repr(name)


def _generic_base_name(class_name: str) -> str | None:
    """Return the base name of a subscripted generic name such as 'Box[int]', or None."""
    if "[" in class_name and class_name.endswith("]"):
        return class_name[: class_name.index("[")]
    return None


def _validate_importable_packages(importable_packages: Any) -> frozenset[str]:
    """Check the `importable_packages` argument and freeze it."""
    if isinstance(importable_packages, (str, bytes)):
        msg = "importable_packages must be a collection of package names, not a single string"
        raise TypeError(msg)
    if not isinstance(importable_packages, Iterable):
        msg = f"importable_packages must be a collection of package names, got {type(importable_packages).__name__}"
        raise TypeError(msg)
    packages: list[str] = []
    for entry in cast(Iterable[Any], importable_packages):
        if not isinstance(entry, str):
            msg = f"importable_packages entries must be strings, got {type(entry).__name__}"
            raise TypeError(msg)
        if not all(segment.isidentifier() for segment in entry.split(".")):
            msg = f"importable_packages entry {entry!r} is not a dotted package name"
            raise ValueError(msg)
        packages.append(entry)
    return frozenset(packages)


def _classify(the_class: type[Any]) -> list[_DecodeStrategy]:
    """Return, in order, the strategies the decoder tries to rebuild an instance of `the_class`.

    Hooks come first (a registered decoder, then `__json_decode__`), followed by exactly one
    structural strategy. Permissive mode walks the whole list; safe mode takes the first entry only.
    """
    strategies: list[_DecodeStrategy] = []
    if the_class in UniversalJSONDecoder._decoders:  # pyright: ignore[reportPrivateUsage]
        strategies.append(_DecodeStrategy.REGISTERED_DECODER)
    if hasattr(the_class, "__json_decode__"):
        strategies.append(_DecodeStrategy.JSON_DECODE_HOOK)
    if issubclass(the_class, RootModel):
        strategies.append(_DecodeStrategy.ROOT_MODEL)
    elif issubclass(the_class, Enum):
        strategies.append(_DecodeStrategy.ENUM)
    elif issubclass(the_class, BaseModel):
        strategies.append(_DecodeStrategy.BASE_MODEL)
    elif is_pydantic_dataclass(the_class):
        strategies.append(_DecodeStrategy.PYDANTIC_DATACLASS)
    else:
        strategies.append(_DecodeStrategy.GENERIC_CONSTRUCTOR)
    return strategies


def _construction_override(the_class: type[Any], strategy: _DecodeStrategy) -> str | None:
    """Name the construction step `the_class` overrides, for a class safe mode rebuilds structurally.

    Validation is not enough on its own: pydantic's `model_validate` runs a model's own `__init__`
    and `__new__`, a model may override `model_validate` itself, and pydantic-settings' `BaseSettings.__init__` reads the files its arguments
    name. Safe mode therefore rebuilds a pydantic class only when constructing it runs nothing but
    pydantic, and an enum only when its lookups are the stdlib's. Returns None when nothing is
    overridden.
    """
    match strategy:
        case _DecodeStrategy.ROOT_MODEL:
            if the_class.__init__ is not _ROOT_MODEL_INIT:
                return "__init__"
            return _model_validate_override(the_class) or _pydantic_new_or_call_override(the_class)
        case _DecodeStrategy.BASE_MODEL:
            if the_class.__init__ is not _BASE_MODEL_INIT:
                return "__init__"
            return _model_validate_override(the_class) or _pydantic_new_or_call_override(the_class)
        case _DecodeStrategy.PYDANTIC_DATACLASS:
            # Safe mode runs the dataclass's validator directly and never calls its __init__.
            return _pydantic_new_or_call_override(the_class)
        case _DecodeStrategy.ENUM:
            metaclass = type(the_class)
            if metaclass.__call__ is not _ENUM_META_CALL:
                return "its metaclass __call__"
            if getattr(metaclass, "__getitem__", None) is not _ENUM_META_GETITEM:
                return "its metaclass __getitem__"
            return None
        case _DecodeStrategy.REGISTERED_DECODER | _DecodeStrategy.JSON_DECODE_HOOK | _DecodeStrategy.GENERIC_CONSTRUCTOR:
            return None


def _model_validate_override(the_class: type[Any]) -> str | None:
    """Name the `model_validate` override of a pydantic model, or None: safe mode rebuilds a model by calling it."""
    if getattr(the_class.model_validate, "__func__", None) is not _BASE_MODEL_VALIDATE_FUNC:
        return "model_validate"
    return None


def _pydantic_new_or_call_override(the_class: type[Any]) -> str | None:
    """Name the `__new__` or metaclass `__call__` override of a pydantic class, or None.

    pydantic's validator runs an overridden `__new__`; calling the class runs the metaclass `__call__`.
    """
    if the_class.__new__ is not object.__new__:
        return "__new__"
    if type(the_class).__call__ is not type.__call__:
        return "its metaclass __call__"
    return None


class UniversalJSONDecoder(json.JSONDecoder):
    """
    A universal JSON decoder for Python objects. To be used with JSON strings created
    using the `UniversalJSONEncoder`. Will use static methods `__json_decode__()` if
    provided in your custom classes. It will use the default JSON decoder whenever
    possible and then try multiple techniques to decode the provided objects.

    In addition, it is possible to register functions for types over which you have
    no control (standard / external library types). For this, use static method
    `UniversalJSONDecoder.register()`.

    By default the decoder is permissive: a class marker may name any module, which is
    imported if needed, and a class with no better strategy is rebuilt by calling it with
    the payload's keys. That executes code chosen by whoever wrote the JSON. With
    `safe=True`, a marker can only cause an import inside the packages listed in
    `importable_packages`, and only classes kajson rebuilds by validation or by a decoding
    hook are rebuilt; anything else raises `KajsonDecoderError`.

    How to use this class:
        `json.loads(s, cls=UniversalJSONDecoder)`
                        OR
        `kajson.loads(s)`
                        OR, for JSON you did not write yourself,
        `kajson.loads(s, safe=True, importable_packages=["my_app.models"])`
    """

    # The registered decoding functions:
    _decoders: ClassVar[dict[type[Any], Callable[[dict[str, Any]], Any]]] = {}

    @staticmethod
    def register(obj_type: type[T], decoding_function: Callable[[dict[str, Any]], T]) -> None:
        """
        Register a function as a decoder for the provided type/class. The provided
        decoder should take a single argument (the raw dict to deserialise) and return
        an instance of that object.
        Passing a new decoding function to a type already registered will overwrite
        the previously registered decoding function.
        Args:
            type (obj_type): The type to be decoded by the provided decoder. Can be
                easily obtained by simply providing a class directly.
            decoding_function (function): The function to use as a decoder for the
                provided type. Takes a single argument, a returns an object.
        """
        if not isinstance(obj_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("Expected a type/class, a %s was passed instead." % type(obj_type))
        if not callable(decoding_function):
            raise TypeError("Expected a function, a %s was passed instead." % type(decoding_function))

        UniversalJSONDecoder._decoders[obj_type] = decoding_function

    @classmethod
    def clear_decoders(cls) -> None:
        """Clear all registered decoders. Primarily for testing purposes."""
        cls._decoders.clear()

    @classmethod
    def is_decoder_registered(cls, obj_type: type[Any]) -> bool:
        """Check if a decoder is registered for the given type. Primarily for testing purposes."""
        return obj_type in cls._decoders

    @classmethod
    def get_registered_decoder(cls, obj_type: type[Any]) -> Callable[[dict[str, Any]], Any] | None:
        """Get the registered decoder for the given type. Primarily for testing purposes."""
        return cls._decoders.get(obj_type)

    # Required to redirect the hook for decoding.
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Constructor redirecting the hook for decoding JSON objects.

        Takes, besides the arguments of `json.JSONDecoder` (`strict` among them):
            class_registry: An explicit class registry, consulted before any other source.
            safe: Refuse imports outside `importable_packages` and classes that are not
                rebuilt by validation or by a decoding hook. Defaults to False.
            importable_packages: Packages under which safe mode may import a module to
                resolve a class. Only allowed with `safe=True`.

        Raises:
            TypeError: When `safe` is not a bool, or `importable_packages` is a string or
                holds something other than strings.
            ValueError: When `importable_packages` is given without `safe=True`, or holds
                an entry that is not a dotted package name.
        """
        self._class_registry: ClassRegistryAbstract | None = kwargs.pop("class_registry", None)
        safe = kwargs.pop("safe", False)
        if not isinstance(safe, bool):
            msg = f"safe must be a bool, got {type(safe).__name__}"
            raise TypeError(msg)
        importable_packages = _validate_importable_packages(kwargs.pop("importable_packages", ()))
        if importable_packages and not safe:
            msg = "importable_packages only applies with safe=True; without it, every module is importable"
            raise ValueError(msg)
        self._safe: bool = safe
        self._importable_packages: frozenset[str] = importable_packages
        json.JSONDecoder.__init__(self, object_hook=self.universal_decoder, *args, **kwargs)
        self.logger = logging.getLogger(DECODER_LOGGER_CHANNEL_NAME)

    def log(self, message: str) -> None:
        self.logger.debug(message)

    def universal_decoder(self, the_dict: dict[str, Any]) -> Any:
        """
        Universal decoder for JSON objects encoded using the UniversalJSONEncoder.

        A dict without a `__class__` marker is returned as is. For a dict with one, the
        decoder checks the marker, resolves the class it names (explicit registry, then an
        imported module, then the global registry, then an import), checks that the result
        is a class and rebuilds the object. Permissive mode tries a registered decoder,
        `__json_decode__`, the pydantic or enum strategy, then the class's constructor
        with the dict's keys, the no-argument constructor with `__dict__` replaced, and
        finally returns the raw dict. Safe mode uses only the first strategy that applies
        and refuses a class whose first strategy is the constructor.

        Args:
            the_dict (dict): A raw dictionary obtained from the JSON string to be made
                into a beautiful Python object.
        Return:
            object - A Python object corresponding to the provided JSON object.
        Raises:
            KajsonDecoderError: When the marker is malformed, the class cannot be
                resolved or is not a class, safe mode refuses it, or rebuilding fails.
        """
        # Base object:
        if "__class__" not in the_dict:
            return the_dict

        class_name, module_name = self._pop_marker(the_dict)
        the_class = self._resolve_marker_class(class_name=class_name, module_name=module_name)
        if not isinstance(the_class, type):
            msg = f"Class marker {_quote_name(class_name)} in module {_quote_name(module_name)} does not name a class"
            raise KajsonDecoderError(msg)

        if self._safe:
            return self._apply_safe_strategy(the_class, class_name, module_name, the_dict)
        return self._apply_decoder_strategies(the_class, class_name, the_dict)

    @staticmethod
    def _pop_marker(the_dict: dict[str, Any]) -> tuple[str, str]:
        """Remove and return the `__class__` and `__module__` marker, checking its shape."""
        class_name = the_dict.pop("__class__")
        if "__module__" not in the_dict:
            msg = "Malformed class marker: '__class__' without '__module__'"
            raise KajsonDecoderError(msg)
        module_name = the_dict.pop("__module__")
        if not isinstance(class_name, str) or not isinstance(module_name, str):
            msg = (
                f"Malformed class marker: '__class__' and '__module__' must be strings, "
                f"got {type(class_name).__name__} and {type(module_name).__name__}"
            )
            raise KajsonDecoderError(msg)
        return class_name, module_name

    def _lookup_in_module(self, module: Any, name: str) -> Any:
        """Return the attribute `name` of `module`, or `_MISSING`.

        Safe mode reads the module's namespace directly, so that a module-level `__getattr__`,
        which may import submodules lazily, never runs on a payload-supplied name. The encoder
        writes the defining module of a class, whose namespace holds it.
        """
        if self._safe:
            namespace = getattr(module, "__dict__", None)
            if not isinstance(namespace, dict):
                return _MISSING
            return cast(dict[str, Any], namespace).get(name, _MISSING)
        try:
            return getattr(module, name)
        except AttributeError:
            return _MISSING

    def _lookup_generic_base(self, module: Any, class_name: str) -> Any:
        """For a subscripted generic name absent from its module, look up its base class instead, or return `_MISSING`."""
        base_class_name = _generic_base_name(class_name)
        if base_class_name is None:
            return _MISSING
        self.log(f"Generic type {_quote_name(class_name)} not found in module, trying base class {_quote_name(base_class_name)}")
        return self._lookup_in_module(module, base_class_name)

    @staticmethod
    def _not_found_message(class_name: str, module_name: str, *, where: str) -> str:
        """Say that a class was not found, naming the missing base class of a generic name."""
        base_class_name = _generic_base_name(class_name)
        if base_class_name is not None:
            return f"Generic class {_quote_name(class_name)}: base class {_quote_name(base_class_name)} not found in {where}"
        return f"Class {_quote_name(class_name)} not found in {where}"

    def _may_import(self, module_name: str) -> bool:
        """Whether resolving a class may import `module_name`: always in permissive mode, inside `importable_packages` in safe mode."""
        if not self._safe:
            return True
        return any(module_name == package or module_name.startswith(package + ".") for package in self._importable_packages)

    def _resolve_marker_class(self, *, class_name: str, module_name: str) -> Any:
        """Resolve the object a class marker names. The result is not yet known to be a class."""
        # Step 0: Check explicit registry first (takes priority over sys.modules and dynamic import)
        if self._class_registry is not None:
            explicit_class = self._class_registry.get_class(name=class_name)
            if explicit_class is not None:
                self.log(f"Found class {_quote_name(class_name)} in explicit registry")
                return explicit_class

        # Check if the module is already imported using sys.modules
        if module_name in sys.modules:
            module = sys.modules[module_name]
            found = self._lookup_in_module(module, class_name)
            if found is not _MISSING:
                return found
            base_class = self._lookup_generic_base(module, class_name)
            if base_class is not _MISSING:
                return base_class
            # Module is loaded but class is not in it — fall through to global registry
            # before raising. This handles dynamically built classes (e.g. with pydantic's
            # create_model) whose __module__ names a loaded module that does not hold them,
            # such as 'builtins', and that were registered in the global ClassRegistry.
            self.log(f"Class {_quote_name(class_name)} not found in module {_quote_name(module_name)}, checking global registry")
            registered_class = KajsonManager.get_class_registry().get_class(name=class_name)
            if registered_class is not None:
                return registered_class
            error_msg = self._not_found_message(class_name, module_name, where=f"module {_quote_name(module_name)} or global registry")
            raise KajsonDecoderError(error_msg)

        if registered_class := KajsonManager.get_class_registry().get_class(name=class_name):
            self.log(f"Found class {_quote_name(class_name)} in registry")
            return registered_class

        if not self._may_import(module_name):
            msg = (
                f"Refusing to import module {_quote_name(module_name)} to resolve class {_quote_name(class_name)}: "
                "safe mode imports only modules inside importable_packages"
            )
            raise KajsonDecoderError(msg)
        self.log(f"Module {_quote_name(module_name)} not found either in imported modules or registry, now importing")
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            error_msg = f"Error while trying to import module {_quote_name(module_name)}: {exc}"
            self.log(error_msg)
            raise KajsonDecoderError(error_msg) from exc
        self.log(f"Module {_quote_name(module_name)} imported")
        found = self._lookup_in_module(module, class_name)
        if found is not _MISSING:
            return found
        base_class = self._lookup_generic_base(module, class_name)
        if base_class is not _MISSING:
            return base_class
        error_msg = self._not_found_message(class_name, module_name, where=f"module {_quote_name(module_name)}")
        raise KajsonDecoderError(error_msg)

    def _apply_decoder_strategies(self, the_class: type[Any], class_name: str, the_dict: dict[str, Any]) -> Any:
        """Rebuild an object in permissive mode, walking every strategy that applies to the resolved class.

        A failed hook moves on to the next strategy only when `IS_DECODER_FALLBACK_ENABLED` is set.
        Subclasses that replace class resolution call this method to keep kajson's rebuild.
        """
        for strategy in _classify(the_class):
            result = self._rebuild(strategy, the_class, class_name, the_dict, safe=False)
            if not isinstance(result, _Declined):
                return result
        # The last strategy, structural, never declines.
        return the_dict

    def _apply_safe_strategy(self, the_class: type[Any], class_name: str, module_name: str, the_dict: dict[str, Any]) -> Any:
        """Rebuild an object in safe mode: refuse unless the first strategy rebuilds by validation or a hook, then use it alone."""
        strategy = _classify(the_class)[0]
        qualified = f"{_quote_name(module_name)}.{_quote_name(class_name)}"
        if not strategy.is_allowed_in_safe_mode:
            msg = (
                f"Refusing to instantiate {qualified}: safe mode does not call a class's constructor with the payload's keys. "
                f"It rebuilds {SAFE_MODE_REBUILDABLE_KINDS}."
            )
            raise KajsonDecoderError(msg)
        if (override := _construction_override(the_class, strategy)) is not None:
            msg = (
                f"Refusing to instantiate {qualified}: safe mode rebuilds a {strategy.kind_label} "
                f"only when constructing it runs nothing but the library's own code, and this class overrides {override}."
            )
            raise KajsonDecoderError(msg)
        try:
            result = self._rebuild(strategy, the_class, class_name, the_dict, safe=True)
        except KajsonDecoderError:
            raise
        except Exception as exc:
            # Unbounded surface: the rebuild runs the class's validators, model_post_init,
            # __post_init__, _missing_ and decoding hooks. Safe-mode callers catch KajsonDecoderError only.
            msg = f"Could not decode {qualified}: {type(exc).__name__}: {exc}"
            raise KajsonDecoderError(msg) from exc
        if isinstance(result, _Declined):  # pragma: no cover - safe rebuilds never decline
            msg = f"Could not decode {qualified}"
            raise KajsonDecoderError(msg)
        return result

    def _rebuild(self, strategy: _DecodeStrategy, the_class: type[Any], class_name: str, the_dict: dict[str, Any], *, safe: bool) -> Any:
        """Rebuild an object with one strategy. Returns `_DECLINED` when a permissive hook gives way to the next strategy."""
        match strategy:
            case _DecodeStrategy.REGISTERED_DECODER:
                return self._rebuild_with_registered_decoder(the_class, class_name, the_dict, safe=safe)
            case _DecodeStrategy.JSON_DECODE_HOOK:
                return self._rebuild_with_json_decode_hook(the_class, class_name, the_dict, safe=safe)
            case _DecodeStrategy.ROOT_MODEL:
                return self._rebuild_root_model(cast(type[RootModel[Any]], the_class), class_name, the_dict, safe=safe)
            case _DecodeStrategy.ENUM:
                return self._rebuild_enum(cast(type[Enum], the_class), class_name, the_dict)
            case _DecodeStrategy.BASE_MODEL:
                return self._rebuild_base_model(cast(type[BaseModel], the_class), class_name, the_dict, safe=safe)
            case _DecodeStrategy.PYDANTIC_DATACLASS:
                return self._rebuild_pydantic_dataclass(the_class, class_name, the_dict, safe=safe)
            case _DecodeStrategy.GENERIC_CONSTRUCTOR:
                return self._rebuild_with_constructor(the_class, the_dict)

    @staticmethod
    def _hook_failed(error_msg: str, exc: Exception, *, safe: bool) -> _Declined:
        """Handle a failed decoding hook: give way to the next strategy if the permissive fallback allows it, raise otherwise."""
        if not safe and IS_DECODER_FALLBACK_ENABLED:
            warnings.warn(error_msg + FALLBACK_MESSAGE)
            return _DECLINED
        raise KajsonDecoderError(error_msg) from exc

    def _rebuild_with_registered_decoder(self, the_class: type[Any], class_name: str, the_dict: dict[str, Any], *, safe: bool) -> Any:
        decoder = UniversalJSONDecoder._decoders[the_class]
        try:
            return decoder(the_dict)
        except Exception as exc:
            # Unbounded surface: the decoder is a function a caller registered.
            func_name = getattr(decoder, "__name__", repr(decoder))
            error_msg = f"Could not decode {_quote_name(class_name)} from json because function '{func_name}' failed: '{exc}'."
            return self._hook_failed(error_msg, exc, safe=safe)

    def _rebuild_with_json_decode_hook(self, the_class: type[Any], class_name: str, the_dict: dict[str, Any], *, safe: bool) -> Any:
        try:
            return getattr(the_class, "__json_decode__")(the_dict)
        except Exception as exc:
            # Unbounded surface: the hook is the class's own decoding code.
            error_msg = f"Could not decode {_quote_name(class_name)} from json because static method __json_decode__ failed: '{exc}'."
            return self._hook_failed(error_msg, exc, safe=safe)

    def _rebuild_root_model(self, the_class: type[RootModel[Any]], class_name: str, the_dict: dict[str, Any], *, safe: bool) -> Any:
        if safe:
            # Validate the root value without calling the class: the construction check has
            # already established that the class's construction is pydantic's own.
            if set(the_dict) != {"root"}:
                msg = f"Could not decode {_quote_name(class_name)} pydantic RootModel from json: expected exactly one key, 'root'"
                raise KajsonDecoderError(msg)
            try:
                return the_class.model_validate(the_dict["root"])
            except ValidationError as exc:
                error_msg = f"Could not decode {_quote_name(class_name)} pydantic RootModel from json: {exc}"
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc

        self.log(f"Using dictionary to initialize root of root_model '{the_class}'")
        # for soem reason, calling model_validate directly on the dict does not work:
        # as it builds another layer around the root: {"root": {"root": {}}
        try:
            self.log(f"Creating root model '{the_class}'...")
            root_model_obj = the_class(**the_dict)
            self.log(f"Root model '{the_class}' created: {root_model_obj}")
        except ValidationError as exc:
            # Do NOT include the_dict in the message: payloads may carry secrets
            # (passwords, API keys). The chained exception (from exc) still carries
            # the offending value via pydantic's ValidationError for debugging.
            error_msg = f"Could not decode {_quote_name(class_name)} pydantic RootModel from json: {exc}"
            self.log(error_msg)
            raise KajsonDecoderError(error_msg) from exc

        try:
            self.log(f"Trying to validate root model '{the_class}'...")
            the_class.model_validate(obj=root_model_obj)
            self.log(f"Root model '{the_class}' validated")
            return root_model_obj
        except ValidationError as exc:
            error_msg = f"Could not post validate pydantic RootModel '{the_class}': {exc}"
            self.log(error_msg)
            raise KajsonDecoderError(error_msg) from exc

    def _rebuild_enum(self, the_class: type[Enum], class_name: str, the_dict: dict[str, Any]) -> Any:
        self.log(f"Handling enum class '{the_class}'")
        try:
            # For enums, we need to reconstruct using the enum name or value
            if "_name_" in the_dict:
                # Reconstruct from enum name
                return the_class[the_dict["_name_"]]
            elif "_value_" in the_dict:
                # Reconstruct from enum value
                return the_class(the_dict["_value_"])
            else:
                msg = f"Could not reconstruct enum {_quote_name(class_name)}: missing _name_ or _value_"
                raise KajsonDecoderError(msg)
        except (KeyError, ValueError, TypeError) as exc:
            # TypeError: an unhashable name, such as a list, cannot be looked up.
            # Do NOT include the_dict in the message: payloads may carry secrets.
            error_msg = f"Could not reconstruct enum {_quote_name(class_name)}: {exc}"
            self.log(error_msg)
            raise KajsonDecoderError(error_msg) from exc

    def _rebuild_base_model(self, the_class: type[BaseModel], class_name: str, the_dict: dict[str, Any], *, safe: bool) -> Any:
        self.log(f"Using model_validate for class '{the_class}'")
        try:
            return the_class.model_validate(the_dict)
        except ValidationError as exc:
            # Do NOT include the_dict or base_model_obj in messages: payloads may carry
            # secrets (passwords, API keys). The chained exception (from exc) still
            # carries the offending value via pydantic's ValidationError for debugging.
            error_msg = f"Could not model_validate pydantic BaseModel '{the_class}': {exc}"
            self.log(error_msg)
            if safe:
                # Safe mode never falls back to calling the class with the payload's keys.
                raise KajsonDecoderError(error_msg) from exc
            try:
                base_model_obj = the_class(**the_dict)
            except ValidationError as exc:
                error_msg = f"Could not instantiate pydantic BaseModel '{the_class}' using kwargs: {exc}"
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc
            try:
                self.log(f"Trying to validate base model '{the_class}'")
                the_class.model_validate(obj=base_model_obj)
                self.log(f"Base model '{the_class}' validated")
                return base_model_obj
            except ValidationError as exc:
                error_msg = f"Could not post validate pydantic BaseModel '{the_class}': {exc}"
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc

    def _rebuild_pydantic_dataclass(self, the_class: type[Any], class_name: str, the_dict: dict[str, Any], *, safe: bool) -> Any:
        self.log(f"Using pydantic dataclass validator for class '{the_class}'")
        try:
            if safe:
                # Run the dataclass's validator directly rather than calling the class.
                if not getattr(the_class, "__pydantic_complete__", False):
                    rebuild_dataclass(the_class, raise_errors=True)
                return the_class.__pydantic_validator__.validate_python(the_dict)
            # Calling the dataclass runs its pydantic validator (validates + coerces).
            return the_class(**the_dict)
        except Exception as exc:
            # Broad by design: the constructor runs user-defined validation and an optional
            # __post_init__, whose exception surface is unbounded (pydantic only wraps
            # ValueError/AssertionError into ValidationError; RuntimeError/TypeError/etc. escape raw).
            # Do NOT include the_dict in the message: payloads may carry secrets.
            error_msg = f"Could not decode pydantic dataclass '{the_class}': {exc}"
            self.log(error_msg)
            raise KajsonDecoderError(error_msg) from exc

    @staticmethod
    def _rebuild_with_constructor(the_class: type[Any], the_dict: dict[str, Any]) -> Any:
        """Permissive mode's last resort. Safe mode refuses a class before reaching it."""
        # Try the constructor with the dictionary as arguments:
        try:
            return the_class(**the_dict)
        except Exception:
            pass

        # Try the default constructor (no arguments)
        # and replace __dict__
        try:
            obj = the_class()
            obj.__dict__ = the_dict
            return obj
        except Exception:
            pass

        # Default, return the raw dict:
        return the_dict
