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

import importlib
import json
import logging
import types
import warnings
from typing import Any, Callable, ClassVar, Dict, Type, TypeVar

from pydantic import BaseModel, RootModel, ValidationError

from kajson.class_registry import class_registry
from kajson.exceptions import KajsonDecoderError
from kajson.sandbox_manager import sandbox_manager

DECODER_LOGGER_CHANNEL_NAME = "kajson.decoder"
DECODER_LOGGER_CHANNEL_NAME_IN_SANDBOX = "kajson.decoder.sandbox"
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
            raise ValueError("Expected a type/class, a %s was passed instead." % type(obj_type))
        if not callable(decoding_function):
            raise ValueError("Expected a function, a %s was passed instead." % type(decoding_function))

        UniversalJSONDecoder._decoders[obj_type] = decoding_function

    # Required to redirect the hook for decoding.
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Constructor redirecting the hook for decoding JSON objects."""
        json.JSONDecoder.__init__(self, object_hook=self.universal_decoder, *args, **kwargs)
        self.logger = logging.getLogger(DECODER_LOGGER_CHANNEL_NAME)

    def log(self, message: str) -> None:
        if sandbox_manager.is_in_sandbox():
            logger = logging.getLogger(DECODER_LOGGER_CHANNEL_NAME_IN_SANDBOX)
            logger.debug(message)
        else:
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

        all_mods = _get_imported_modules()
        if module_name in all_mods:
            the_class = getattr(all_mods[module_name], class_name)
        elif registered_class := class_registry.get_class(name=class_name):
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
            the_class = getattr(m, class_name)

        # Registered decoder if any:
        if the_class in UniversalJSONDecoder._decoders:
            try:
                return UniversalJSONDecoder._decoders[the_class](the_dict)
            except Exception as exc:
                func_name = UniversalJSONDecoder._decoders[the_class].__name__
                error_msg = f"Decoding function '{func_name}' used for type '{the_class}' raised an exception: '{exc}'."
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
            error_msg = f"Static method __json_deconde__ used for type '{the_class}' raised an exception: '{exc}'."
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
                error_msg = f"Error: creating root_model '{the_class}': {exc}\n\nthe_dict:\n{the_dict}"
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc

            try:
                self.log(f"Trying to validate root model '{the_class}' with object '{root_model_obj}'...")
                the_class.model_validate(obj=root_model_obj)
                self.log(f"Root model '{the_class}' validated")
                return root_model_obj
            except ValidationError as exc:
                error_msg = f"Error: post validate root_model '{the_class}': {exc}\n\nthe_dict:\n{the_dict}\n\nroot_model_obj:\n{root_model_obj}"
                self.log(error_msg)
                raise KajsonDecoderError(error_msg) from exc

        if issubclass(the_class, BaseModel):
            self.log(f"Using model_validate for class '{the_class}'")
            try:
                return the_class.model_validate(the_dict)
            except ValidationError as exc:
                error_msg = f"Error: model_validate for '{the_class}': {exc}\n\nthe_dict:\n{the_dict}"
                self.log(error_msg)
                try:
                    base_model_obj = the_class(**the_dict)
                except ValidationError as exc:
                    error_msg = f"Error while trying to instantiate using kwargs '{the_class}': {exc}\n\nthe_dict:\n{the_dict}"
                    self.log(error_msg)
                    raise KajsonDecoderError(error_msg) from exc
                try:
                    self.log(f"Trying to validate base model '{the_class}' with object '{base_model_obj}'")
                    the_class.model_validate(obj=base_model_obj)
                    self.log(f"Base model '{the_class}' validated")
                    return base_model_obj
                except ValidationError as exc:
                    error_msg = (
                        f"Error while trying to post validate base_model '{the_class}': "
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


#########################################################################################
#########################################################################################
#########################################################################################


def _get_imported_modules() -> Dict[str, types.ModuleType]:
    """
    Get all the already imported modules.
    Found here: http://stackoverflow.com/a/4858123/5321016
    Return:
        dict[str:module] - A dictionary of the already imported modules.
            Keys are modules' names.
    """
    result: Dict[str, types.ModuleType] = {}
    for attribute in globals().values():
        if isinstance(attribute, types.ModuleType):
            result[attribute.__name__] = attribute
    return result
