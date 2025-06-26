# SPDX-FileCopyrightText: © 2018 Bastien Pietropaoli
# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
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
from enum import Enum
from typing import Any, Callable, ClassVar, Dict, Type, TypeVar

from pydantic import BaseModel, RootModel, ValidationError

from kajson.exceptions import KajsonDecoderError
from kajson.kajson_manager import KajsonManager

DECODER_LOGGER_CHANNEL_NAME = "kajson.decoder"
IS_DECODER_FALLBACK_ENABLED = False
FALLBACK_MESSAGE = " Trying something else."


T = TypeVar("T")


class UniversalJSONDecoder(json.JSONDecoder):
    """
    A universal JSON decoder for Python objects. To be used with JSON strings created
    using the `UniversalJSONEncoder`. Will use static methods `__json_decode__()` if
    provided in your custom classes. It will use the default JSON decoder whenever
    possible and then try multiple techniques to decode the provided objects.

    In addition, it is possible to register functions for types over which you have
    no control (standard / external library types). For this, use static method
    `UniversalJSONDecoder.register()`.

    How to use this class:
        `json.loads(s, cls=UniversalJSONDecoder)`
                        OR
        `kajson.loads(s)`
    """

    # The registered decoding functions:
    _decoders: ClassVar[Dict[Type[Any], Callable[[Dict[str, Any]], Any]]] = {}

    @staticmethod
    def register(obj_type: Type[T], decoding_function: Callable[[Dict[str, Any]], T]) -> None:
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
    def is_decoder_registered(cls, obj_type: Type[Any]) -> bool:
        """Check if a decoder is registered for the given type. Primarily for testing purposes."""
        return obj_type in cls._decoders

    @classmethod
    def get_registered_decoder(cls, obj_type: Type[Any]) -> Callable[[Dict[str, Any]], Any] | None:
        """Get the registered decoder for the given type. Primarily for testing purposes."""
        return cls._decoders.get(obj_type)

    # Required to redirect the hook for decoding.
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Constructor redirecting the hook for decoding JSON objects."""
        json.JSONDecoder.__init__(self, object_hook=self.universal_decoder, *args, **kwargs)
        self.logger = logging.getLogger(DECODER_LOGGER_CHANNEL_NAME)

    def log(self, message: str) -> None:
        self.logger.debug(message)

    def universal_decoder(self, the_dict: Dict[str, Any]) -> Any:
        """
        Universal decoder for JSON objects encoded using the UniversalJSONEncoder.
        It will try the following methods in order:
         - Default JSON encoder (for known types)
         - Registered encoding function (if one is found)
         - `__json_encode__()` as provided by the custom class (if it's found)
         - Use a constructor taking as argument the raw dictionary
         - Use the default constructor and replace the __dict__ property of the
           object (for custom classes)
        Args:
            the_dict (dict): A raw dictionnary obtained from the JSON string to be made
                into a beautiful Python object.
        Return:
            object - A Python object corresponding to the provided JSON object. If
                nothing could be done for that object, the raw dictionary is returned
                as is.
        """
        # Base object:
        if "__class__" not in the_dict:
            return the_dict

        # Get the class and module of the object:
        class_name = the_dict.pop("__class__")
        module_name = the_dict.pop("__module__")

        the_class: Type[Any]

        # Check if the module is already imported using sys.modules
        if module_name in sys.modules:
            try:
                the_class = getattr(sys.modules[module_name], class_name)
            except AttributeError:
                # If class_name contains type parameters (generic type), try base class
                if "[" in class_name and class_name.endswith("]"):
                    base_class_name = class_name[: class_name.index("[")]
                    self.log(f"Generic type '{class_name}' not found in module, trying base class '{base_class_name}'")
                    the_class = getattr(sys.modules[module_name], base_class_name)
                else:
                    raise KajsonDecoderError(f"Class '{class_name}' not found in module '{module_name}'")
        elif registered_class := KajsonManager.get_class_registry().get_class(name=class_name):
            self.log(f"Found class '{class_name}' in registry")
            the_class = registered_class
        else:
            self.log(f"Module '{module_name}' not found either in imported modules or registry, now importing")
            try:
                m = importlib.import_module(module_name)
            except Exception as exc:
                error_msg = f"Error while trying to import module {module_name}: {exc}"
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc
            self.log(f"Module '{module_name}' imported")
            try:
                the_class = getattr(m, class_name)
            except AttributeError:
                # If class_name contains type parameters (generic type), try base class
                if "[" in class_name and class_name.endswith("]"):
                    base_class_name = class_name[: class_name.index("[")]
                    self.log(f"Generic type '{class_name}' not found in imported module, trying base class '{base_class_name}'")
                    the_class = getattr(m, base_class_name)
                else:
                    raise KajsonDecoderError(f"Class '{class_name}' not found in module '{module_name}'")

        # Registered decoder if any:
        if the_class in UniversalJSONDecoder._decoders:
            try:
                return UniversalJSONDecoder._decoders[the_class](the_dict)
            except Exception as exc:
                func_name = UniversalJSONDecoder._decoders[the_class].__name__
                error_msg = f"Could not decode '{class_name}' from json because function '{func_name}' failed: '{exc}'."
                if IS_DECODER_FALLBACK_ENABLED:
                    warnings.warn(error_msg + FALLBACK_MESSAGE)
                else:
                    raise KajsonDecoderError(error_msg) from exc

        # __json_decode__() static method if any:
        try:
            return getattr(the_class, "__json_decode__")(the_dict)
        except AttributeError:
            pass
        except Exception as exc:
            error_msg = f"Could not decode '{class_name}' from json because static method __json_decode__ failed: '{exc}'."
            if IS_DECODER_FALLBACK_ENABLED:
                warnings.warn(error_msg + FALLBACK_MESSAGE)
            else:
                raise KajsonDecoderError(error_msg) from exc

        if issubclass(the_class, RootModel):
            self.log(f"Using dictionary to initialize root of root_model '{the_class}'")
            # for soem reason, calling model_validate directly on the dict does not work:
            # as it builds another layer around the root: {"root": {"root": {}}
            try:
                self.log(f"Creating root model '{the_class}'...")
                root_model_obj: RootModel[Any] = the_class(**the_dict)
                self.log(f"Root model '{the_class}' created: {root_model_obj}")
            except ValidationError as exc:
                error_msg = f"Could not decode '{class_name}' pydantic RootModel from json: {exc}\n\nthe_dict:\n{the_dict}"
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc

            try:
                self.log(f"Trying to validate root model '{the_class}' with object '{root_model_obj}'...")
                the_class.model_validate(obj=root_model_obj)
                self.log(f"Root model '{the_class}' validated")
                return root_model_obj
            except ValidationError as exc:
                error_msg = (
                    f"Could not post validate pydantic RootModel '{the_class}': {exc}\n\nthe_dict:\n{the_dict}\n\nroot_model_obj:\n{root_model_obj}"
                )
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc

        # Handle Enum classes specially
        if issubclass(the_class, Enum):
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
                    raise KajsonDecoderError(f"Could not reconstruct enum '{class_name}': missing _name_ or _value_")
            except (KeyError, ValueError) as exc:
                error_msg = f"Could not reconstruct enum '{class_name}': {exc}\n\nthe_dict:\n{the_dict}"
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc

        if issubclass(the_class, BaseModel):
            self.log(f"Using model_validate for class '{the_class}'")
            try:
                return the_class.model_validate(the_dict)
            except ValidationError as exc:
                error_msg = f"Could not model_validate pydantic BaseModel '{the_class}': {exc}\n\nthe_dict:\n{the_dict}"
                self.log(error_msg)
                try:
                    base_model_obj = the_class(**the_dict)
                except ValidationError as exc:
                    error_msg = f"Could not instantiate pydantic BaseModel '{the_class}' using kwargs: {exc}\n\nthe_dict:\n{the_dict}"
                    self.log(error_msg)
                    raise KajsonDecoderError(error_msg) from exc
                try:
                    self.log(f"Trying to validate base model '{the_class}' with object '{base_model_obj}'")
                    the_class.model_validate(obj=base_model_obj)
                    self.log(f"Base model '{the_class}' validated")
                    return base_model_obj
                except ValidationError as exc:
                    error_msg = (
                        f"Could not post validate pydantic BaseModel '{the_class}': "
                        f"{exc}\n\nthe_dict:\n{the_dict}\n\nbase_model_obj:\n{base_model_obj}"
                    )
                    self.log(error_msg)
                    raise KajsonDecoderError(error_msg) from exc

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
