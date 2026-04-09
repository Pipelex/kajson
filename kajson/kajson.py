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

import datetime
import enum
import json
from typing import IO, Any, Dict, Union
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from kajson.class_registry import ClassRegistry
from kajson.class_registry_abstract import ClassRegistryAbstract
from kajson.exceptions import KajsonDecoderError
from kajson.json_decoder import UniversalJSONDecoder
from kajson.json_encoder import UniversalJSONEncoder


def _build_registry_from_source(source_code: str) -> ClassRegistry:
    """Build a ClassRegistry from Python source code by exec'ing it and discovering classes.

    Registers both BaseModel subclasses and Enum subclasses so that dynamically
    generated types (e.g. enum classes for choices/constrained fields) can be
    resolved during deserialization.

    WARNING: The source is executed via exec() and can run arbitrary Python code.
    Only pass trusted source code.

    Args:
        source_code: Python source code that defines one or more BaseModel subclasses
            and optionally Enum subclasses.

    Returns:
        A ClassRegistry containing all discovered BaseModel and Enum subclasses.
    """
    namespace: dict[str, Any] = {}
    exec(compile(source_code, "<kajson_class_source>", "exec"), namespace)

    # Collect all user-defined types for forward reference resolution
    all_types: dict[str, Any] = {name: obj for name, obj in namespace.items() if isinstance(obj, type) and not name.startswith("_")}

    # Rebuild models so forward references (from `from __future__ import annotations`)
    # resolve against all generated types including Enum classes
    for name, obj in all_types.items():
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
            try:
                obj.model_rebuild(_types_namespace=all_types)
            except Exception:
                pass  # Best-effort: some models may not need rebuilding

    registry = ClassRegistry()
    for name, obj in all_types.items():
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
            registry.register_class(obj, name=name, should_warn_if_already_registered=False)
        elif isinstance(obj, type) and issubclass(obj, enum.Enum) and obj is not enum.Enum:
            registry.register_class(obj, name=name, should_warn_if_already_registered=False)
    return registry


# ------------------------------------------------
# API similar to the standard library json package
# ------------------------------------------------


def dumps(obj: Any, **kwargs: Any) -> str:
    """
    Serialise a given object into a JSON formatted string. This function
    uses the `UniversalJSONEncoder` instead of the default JSON encoder
    provided in the standard library. Takes the same keyword arguments as
    `json.dumps()` except for `cls` that is used to pass our custom encoder.
    Args:
        obj (object): The object to serialise.
        kwargs (**): Keyword arguments normally passed to `json.dumps()` except
            for `cls`. Unpredictable behaviour might occur if `cls` is passed.
    Return:
        str - The object serialised into a JSON string.
    """
    return json.dumps(obj, cls=UniversalJSONEncoder, **kwargs)


def dump(obj: Any, fp: IO[str], **kwargs: Any) -> None:
    """
    Serialise a given object into a JSON formatted file / stream. This function
    uses the `UniversalJSONEncoder` instead of the default JSON encoder provided
    in the standard library. Takes the same keyword arguments as `json.dump()`
    except for `cls` that is used to pass our custom encoder.
    Args:
        obj (object): The object to serialise.
        fp (file-like object): A .write()-supporting file-like object.
        kwargs (**): Keyword arguments normally passed to `json.dump()` except
            for `cls`. Unpredictable behaviour might occur if `cls` is passed.
    """
    json.dump(obj, fp, cls=UniversalJSONEncoder, **kwargs)


def loads(
    json_string: Union[str, bytes],
    class_registry: ClassRegistryAbstract | None = None,
    class_source_code: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Deserialise a given JSON formatted str into a Python object using the
    `UniversalJSONDecoder`. Takes the same keyword arguments as `json.loads()`
    except for `cls` that is used to pass our custom decoder.
    Args:
        json_string (str): The JSON formatted string to decode.
        class_registry: Optional explicit class registry for resolving classes.
            When provided, the decoder checks this registry first before falling
            back to sys.modules and dynamic import.
        class_source_code: Optional Python source code defining BaseModel classes.
            When provided, the source is exec'd and all discovered BaseModel subclasses
            are registered in a ClassRegistry used during deserialization. If an explicit
            class_registry is also provided, its entries take priority over source-derived ones.
            WARNING: The source is executed via exec() and can run arbitrary Python code.
            Only pass trusted source code.
        kwargs (**): Keyword arguments normally passed to `json.loads()` except
            for `cls`. Unpredictable behaviour might occur if `cls` is passed.
    Return:
        object - A Python object corresponding to the provided JSON formatted string.
    """
    if class_source_code is not None:
        source_registry = _build_registry_from_source(class_source_code)
        if class_registry is not None:
            if isinstance(class_registry, ClassRegistry):
                # Build a temporary merged registry to avoid mutating the caller's registry.
                # Source-derived classes go in first, then explicit registry overwrites.
                merged = ClassRegistry()
                for name, cls in source_registry.root.items():
                    merged.register_class(cls, name=name, should_warn_if_already_registered=False)
                for name, cls in class_registry.root.items():
                    merged.register_class(cls, name=name, should_warn_if_already_registered=False)
                class_registry = merged
            else:
                # Abstract registry with no iteration API — merge into it as best-effort
                for name, cls in source_registry.root.items():
                    if not class_registry.has_class(name):
                        class_registry.register_class(cls, name=name, should_warn_if_already_registered=False)
        else:
            class_registry = source_registry
    if class_registry is not None:
        kwargs["class_registry"] = class_registry
    return json.loads(json_string, cls=UniversalJSONDecoder, **kwargs)


def load(
    fp: IO[str],
    class_registry: ClassRegistryAbstract | None = None,
    class_source_code: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Deserialise a given JSON formatted stream / file into a Python object using
    the `UniversalJSONDecoder`. Takes the same keyword arguments as `json.load()`
    except for `cls` that is used to pass our custom decoder.
    Args:
        fp (file-like object): A .write()-supporting file-like object.
        class_registry: Optional explicit class registry for resolving classes.
            When provided, the decoder checks this registry first before falling
            back to sys.modules and dynamic import.
        class_source_code: Optional Python source code defining BaseModel classes.
            When provided, the source is exec'd and all discovered BaseModel subclasses
            are registered in a ClassRegistry used during deserialization. If an explicit
            class_registry is also provided, its entries take priority over source-derived ones.
            WARNING: The source is executed via exec() and can run arbitrary Python code.
            Only pass trusted source code.
        kwargs (**): Keyword arguments normally passed to `json.load()` except
            for `cls`. Unpredictable behaviour might occur if `cls` is passed.
    Return:
        object - A Python object corresponding to the provided JSON formatted stream / file.
    """
    if class_source_code is not None:
        source_registry = _build_registry_from_source(class_source_code)
        if class_registry is not None:
            if isinstance(class_registry, ClassRegistry):
                merged = ClassRegistry()
                for name, cls in source_registry.root.items():
                    merged.register_class(cls, name=name, should_warn_if_already_registered=False)
                for name, cls in class_registry.root.items():
                    merged.register_class(cls, name=name, should_warn_if_already_registered=False)
                class_registry = merged
            else:
                for name, cls in source_registry.root.items():
                    if not class_registry.has_class(name):
                        class_registry.register_class(cls, name=name, should_warn_if_already_registered=False)
        else:
            class_registry = source_registry
    if class_registry is not None:
        kwargs["class_registry"] = class_registry
    return json.load(fp, cls=UniversalJSONDecoder, **kwargs)


#########################################################################################
#########################################################################################
#########################################################################################


# --------------------------------
# Some useful encoders / decoders:
# --------------------------------


# other implementation using more recent zoneinfo, without the need for pytz (untested):
def json_encode_timezone(t: ZoneInfo) -> Dict[str, Any]:
    """Encoder for timezones (using zoneinfo from Python 3.9+)."""
    return {"zone": t.key}


UniversalJSONEncoder.register(ZoneInfo, json_encode_timezone)


def json_decode_timezone(obj_dict: Dict[str, Any]) -> ZoneInfo:
    """Decoder for timezones (using zoneinfo from Python 3.9+)."""
    return ZoneInfo(obj_dict["zone"])


UniversalJSONDecoder.register(ZoneInfo, json_decode_timezone)


#########################################################################################
def json_encode_date(d: datetime.date) -> Dict[str, str]:
    """Encoder for dates (from module datetime)."""
    return {"date": str(d)}


UniversalJSONEncoder.register(datetime.date, json_encode_date)


def json_decode_date(obj_dict: Dict[str, str]) -> datetime.date:
    """Decoder for dates (from module datetime)."""
    # Split date string into parts and convert to integers
    year, month, day = map(int, obj_dict["date"].split("-"))
    return datetime.date(year, month, day)


UniversalJSONDecoder.register(datetime.date, json_decode_date)

#########################################################################################


def json_encode_datetime(datetime_value: datetime.datetime) -> Dict[str, Any]:
    """Encoder for datetimes (from module datetime)."""
    tzinfo = str(datetime_value.tzinfo) if datetime_value.tzinfo else None
    # Ensure year is always formatted as 4 digits for cross-platform compatibility
    datetime_str = (
        f"{datetime_value.year:04d}-{datetime_value.month:02d}-{datetime_value.day:02d} "
        f"{datetime_value.hour:02d}:{datetime_value.minute:02d}:{datetime_value.second:02d}.{datetime_value.microsecond:06d}"
    )
    return {"datetime": datetime_str, "tzinfo": tzinfo}


UniversalJSONEncoder.register(datetime.datetime, json_encode_datetime)


def json_decode_datetime(obj_dict: Dict[str, Any]) -> datetime.datetime:
    """Decoder for datetimes (from module datetime)."""
    if datetime_str := obj_dict.get("datetime"):
        dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
    else:
        raise KajsonDecoderError("Could not decode datetime from json: datetime field is required")

    if tzinfo_str := obj_dict.get("tzinfo"):
        dt = dt.replace(tzinfo=ZoneInfo(tzinfo_str))
    return dt


UniversalJSONDecoder.register(datetime.datetime, json_decode_datetime)

#########################################################################################


def json_encode_time(t: datetime.time) -> Dict[str, Any]:
    """Encoder for times (from module datetime)."""
    return {"time": t.strftime("%H:%M:%S.%f"), "tzinfo": t.tzinfo}


UniversalJSONEncoder.register(datetime.time, json_encode_time)


def json_decode_time(d: Dict[str, Any]) -> datetime.time:
    """Decoder for times (from module datetime)."""
    # Split time string into parts
    time_parts = d["time"].split(":")
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    # Handle seconds and milliseconds
    seconds_parts = time_parts[2].split(".")
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1])

    return datetime.time(hours, minutes, seconds, milliseconds, tzinfo=d["tzinfo"])


UniversalJSONDecoder.register(datetime.time, json_decode_time)

#########################################################################################


def json_encode_timedelta(t: datetime.timedelta) -> Dict[str, float]:
    """Encoder for timedeltas (from module datetime)."""
    return {"seconds": t.total_seconds()}


UniversalJSONEncoder.register(datetime.timedelta, json_encode_timedelta)
# Won't require a decoder since "seconds" will be automatically passed to a constructor.
