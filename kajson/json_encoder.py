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

import json
import logging
import re
import warnings
from typing import Any, Callable, ClassVar, Dict, Type, TypeVar, cast

from typing_extensions import override

import __main__
from kajson.exceptions import UnijsonEncoderError
from kajson.sandbox_manager import sandbox_manager

ENCODER_LOGGER_CHANNEL_NAME = "kajson.encoder"
ENCODER_LOGGER_CHANNEL_NAME_IN_SANDBOX = "kajson.encoder.sandbox"
IS_ENCODER_FALLBACK_ENABLED = False
FALLBACK_MESSAGE = " Trying something else."


T = TypeVar("T")


class UniversalJSONEncoder(json.JSONEncoder):
    """
    A universal JSON encoder for Python objects. This encoder will work with
    simple custom objects by default and can automatically take into account methods
    `__json_encoder__()` defined in custom classes if implemented correctly. Those
    methods should return a dictionnary (with only strings as keys) and take only
    `self` as an argument.

    In addition, it is possible to register functions for types over which you have
    no control (standard / external library types). For this, use static method
    `UniversalJSONEncoder.register()`.

    The encoder adds attributes `__module__` and `__class__` to the resulting JSON
    objects to enable the identification of the object from which they were constructed.
    They both can be added directly into your encoder to use the same encoder for
    multiple objects (by setting it to a superclass for instance). See the encoders
    for timezones for an example of this. If your encoder already sets them, then they
    won't be modified in this universal encoder. Your values will stay.

    How to use this class:
        `json.dumps(obj, cls=UniversalJSONEncoder)`
                        OR
        `kajson.dumps(obj)`
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(ENCODER_LOGGER_CHANNEL_NAME)

    def log(self, message: str) -> None:
        if sandbox_manager.is_in_sandbox():
            logger = logging.getLogger(ENCODER_LOGGER_CHANNEL_NAME_IN_SANDBOX)
            logger.debug(message)
        else:
            self.logger.debug(message)

    # The registered encoding functions:
    _encoders: ClassVar[Dict[Type[Any], Callable[[Any], Dict[str, Any]]]] = {}

    @staticmethod
    def register(obj_type: Type[T], encoding_function: Callable[[T], Dict[str, Any]]) -> None:
        """
        Register a function as an encoder for the provided type/class. The provided
        encoder should take a single argument (the object to serialise) and return
        a JSON serialisable dictionnary (by the standard of this serialiser).
        Passing a new encoding function to a type already registered will overwrite
        the previously registered encoding function.
        Args:
            type (obj_type): The type to be encoded by the provided encoder. Can be
                easily obtained by simply providing a class directly.
            encoding_function (function): The function to use as an encoder for the
                provided type. Takes a single argument, a returns a dictionnary.
        """
        if not isinstance(obj_type, type):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ValueError("Expected a type/class, a %s was passed instead." % type(obj_type))
        if not callable(encoding_function):
            raise ValueError("Expected a function, a %s was passed instead." % type(encoding_function))

        UniversalJSONEncoder._encoders[obj_type] = encoding_function

    # argument must be named "o" to override the default method
    @override
    def default(self, o: Any) -> Dict[str, Any]:
        """
        Extends the default behaviour of the default JSON encoder. It will try
        the different methods to encode the provided object in the following order:
         - Default JSON encoder (for known types)
         - Registered encoding function (if one is found)
         - `__json_encode__()` as provided by the custom class (if it's found)
         - Use the default __dict__ property of the object (for custom classes)
        Args:
            o (object): The object to serialise.
        Return:
            dict - A dictionnary of JSON serialisable objects.
        Raises:
            TypeError - If none of the methods worked.
        """
        obj: Any = o
        # Default JSON encoder:
        try:
            return cast(Dict[str, Any], json.JSONEncoder.default(self, obj))
        except TypeError:
            pass

        already_encoded = False
        the_dict: Dict[str, Any] = {}

        # Use a registered encoding function:
        if type(obj) in UniversalJSONEncoder._encoders:
            try:
                the_dict = UniversalJSONEncoder._encoders[type(obj)](obj)
                already_encoded = True
            except Exception as exc:
                func_name = UniversalJSONEncoder._encoders[type(obj)].__name__
                error_msg = f"Encoding function {func_name} used for type '{type(obj)}' raised an exception: {exc}."
                if IS_ENCODER_FALLBACK_ENABLED:
                    warnings.warn(error_msg + FALLBACK_MESSAGE)
                else:
                    raise UnijsonEncoderError(error_msg) from exc

        # Trying to use __json_encode__():
        if not already_encoded:
            try:
                the_dict = obj.__json_encode__()  # type: ignore
                already_encoded = True
            except AttributeError:  # No method __json_encode__() found
                pass
            except Exception as exc:
                error_msg = f"Method __json_encode__() used for type '{type(obj)}' raised an exception."
                if IS_ENCODER_FALLBACK_ENABLED:
                    warnings.warn(error_msg + FALLBACK_MESSAGE)
                else:
                    raise UnijsonEncoderError(error_msg) from exc

        # Trying the default __dict__ attribute:
        if not already_encoded:
            try:
                the_dict = dict(obj.__dict__)  # type: ignore
                already_encoded = True
            except AttributeError:
                pass

        # If nothing worked, raise an exception like the default JSON encoder would:
        if not already_encoded:
            raise TypeError(f"Type {type(obj)} is not JSON serializable. Value: {obj}")

        # Add the metadata used to reconstruct the object (if necessary):
        if "__class__" not in the_dict:
            the_dict["__class__"] = str(obj.__class__.__name__)
        if "__module__" not in the_dict:
            the_dict["__module__"] = _get_object_module(obj)

        return the_dict


#########################################################################################
#########################################################################################
#########################################################################################


def _get_object_module(obj: Any) -> str:
    """
    Get the name of the module from which the given object was created.
    Args:
        obj (object): Any object.
    Return:
        str - The name of the module from which the given object was created.
    """
    try:
        module_name = str(obj.__module__)
    except AttributeError:
        module_name = _get_type_module(obj.__class__)
    if module_name == "__main__":
        module_name = __main__.__file__[:-3]  # Prevents having __main__ as a module.
    return module_name

    # Remark 1: Builtin objects don't have a __module__ attribute.
    # Remark 2: inspect.getmodule(obj) should work but it doesn't.


def _get_type_module(the_type: Type[Any]) -> str:
    """
    Get the name of the module containing the given type.
    Args:
        t (type): The type for which the module is requested.
    Return:
        str - The name of the module containing the given type.
    """
    # 1) Extract the name of the module from str(type).
    # 2) Get the chain of submodules separated by dots.
    # 3) Join them together while getting rid of the last one.
    # Expressions used to find module names:
    __class_expression = re.compile(r"^<class '([a-zA-Z0-9._]*)'>")
    __type_expression = re.compile(r"^<type '([a-zA-Z0-9._]*)'>")
    the_type_str = str(the_type)
    if search_result := __class_expression.search(the_type_str):
        return ".".join(search_result.group(1).split(".")[:-1])
    elif search_result := __type_expression.search(the_type_str):
        return ".".join(search_result.group(1).split(".")[:-1])
    else:
        return "builtins"
