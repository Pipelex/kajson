# Decoder API Reference

The decoder module provides classes and utilities for deserializing JSON back to Python objects with type reconstruction.

## UniversalJSONDecoder

The main decoder class that extends `json.JSONDecoder` to reconstruct original Python types.

### Class Definition

```python
class UniversalJSONDecoder(json.JSONDecoder):
    """Enhanced JSON decoder with support for type reconstruction"""
```

### Constructor

```python
def __init__(
    self,
    *,
    object_hook: Callable[[dict[str, Any]], Any] | None = None,
    parse_float: Callable[[str], Any] | None = None,
    parse_int: Callable[[str], Any] | None = None,
    parse_constant: Callable[[str], Any] | None = None,
    strict: bool = True,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None
) -> None
```

**Parameters:** Same as `json.JSONDecoder`, with enhanced object_hook functionality

### Methods

#### decode

```python
def decode(self, s: str) -> Any
```

Decode a JSON document to a Python object with type reconstruction.

**Parameters:**
- `s`: JSON string to decode

**Returns:** Reconstructed Python object

**Raises:**
- `JSONDecodeError`: For invalid JSON syntax
- `KajsonDecoderError`: For type reconstruction failures

### Class Methods

#### register

```python
@classmethod
def register(
    cls,
    type_class: Type,
    decoder: Callable[[dict], Any]
) -> None
```

Register a custom decoder function for a specific type.

**Parameters:**
- `type_class`: The Python type to register
- `decoder`: Function that reconstructs instances from a dict

**Example:**

```python
from decimal import Decimal

def decode_decimal(data: dict) -> Decimal:
    if "__decimal__" not in data:
        raise ValueError("Invalid decimal data")
    return Decimal(data["__decimal__"])

kajson.UniversalJSONDecoder.register(Decimal, decode_decimal)
```

#### unregister

```python
@classmethod
def unregister(cls, type_class: Type) -> None
```

Remove a previously registered decoder for a type.

**Parameters:**
- `type_class`: The type to unregister

#### get_registered_types

```python
@classmethod
def get_registered_types(cls) -> List[Type]
```

Get a list of all registered types.

**Returns:** List of types with custom decoders

## Built-in Decoders

Kajson includes built-in decoders for common types:

### DateTime Decoder

```python
def json_decode_datetime(obj_dict: Dict[str, Any]) -> datetime.datetime:
    """Decoder for datetimes (from module datetime)."""
    if datetime_str := obj_dict.get("datetime"):
        dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
    else:
        raise KajsonDecoderError("Could not decode datetime from json: datetime field is required")

    if tzinfo_str := obj_dict.get("tzinfo"):
        dt = dt.replace(tzinfo=ZoneInfo(tzinfo_str))
    return dt
```

### Date Decoder

```python
def json_decode_date(obj_dict: Dict[str, str]) -> datetime.date:
    """Decoder for dates (from module datetime)."""
    # Split date string into parts and convert to integers
    year, month, day = map(int, obj_dict["date"].split("-"))
    return datetime.date(year, month, day)
```

### Time Decoder

```python
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
```

### Timedelta Decoder

```python
# Timedelta objects are automatically reconstructed from the "seconds" field
# No explicit decoder needed - the constructor handles it directly
```

## Custom Decoder Implementation

### Basic Custom Decoder

```python
import kajson
from typing import Dict, Any

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

def decode_point(data: Dict[str, Any]) -> Point:
    if "__point__" not in data:
        raise ValueError("Not a Point object")
    return Point(data["x"], data["y"])

# Register the decoder
kajson.UniversalJSONDecoder.register(Point, decode_point)

# Now Point objects can be deserialized
json_str = '{"__point__": true, "x": 3.14, "y": 2.71}'
p = kajson.loads(json_str)
assert isinstance(p, Point)
```

### Decoder with Validation

```python
def decode_positive_int(data: Dict[str, Any]) -> PositiveInt:
    if "__positive_int__" not in data:
        raise ValueError("Not a PositiveInt object")
    
    value = data["__positive_int__"]
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"Invalid positive integer: {value}")
    
    return PositiveInt(value)

class PositiveInt:
    def __init__(self, value: int):
        if value <= 0:
            raise ValueError("Must be positive")
        self.value = value

kajson.UniversalJSONDecoder.register(PositiveInt, decode_positive_int)
```

### Decoder with Error Recovery

```python
def decode_with_fallback(data: Dict[str, Any]) -> Any:
    """Decoder that provides fallback for missing data"""
    try:
        if "__custom__" in data:
            # Try to reconstruct custom object
            return CustomClass(**data.get("fields", {}))
    except Exception as e:
        # Log error and return dict as fallback
        print(f"Failed to decode custom object: {e}")
        return data
```

## Advanced Decoding Patterns

### Recursive Type Decoding

```python
from typing import List, Optional, Dict, Any

class TreeNode:
    def __init__(self, value: Any, children: Optional[List["TreeNode"]] = None):
        self.value = value
        self.children = children or []

def decode_tree_node(data: Dict[str, Any]) -> TreeNode:
    if "__tree_node__" not in data:
        raise ValueError("Not a TreeNode")
    
    # Children will be automatically decoded recursively
    return TreeNode(
        value=data["value"],
        children=data.get("children", [])
    )

kajson.UniversalJSONDecoder.register(TreeNode, decode_tree_node)
```

### Type-Safe Decoding

```python
from typing import TypeVar, Type

T = TypeVar('T')

def safe_decode(
    json_str: str,
    expected_type: Type[T]
) -> T:
    """Decode with type checking"""
    result = kajson.loads(json_str)
    
    if not isinstance(result, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, "
            f"got {type(result).__name__}"
        )
    
    return result

# Usage
user_json = '{"name": "Alice", "__class__": "User", "__module__": "__main__"}'
user = safe_decode(user_json, User)  # Type-checked
```

### Polymorphic Decoding

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius
    
    def area(self) -> float:
        return 3.14159 * self.radius ** 2

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
    
    def area(self) -> float:
        return self.width * self.height

def decode_shape(data: Dict[str, Any]) -> Shape:
    """Decode different shape types"""
    if "__circle__" in data:
        return Circle(data["radius"])
    elif "__rectangle__" in data:
        return Rectangle(data["width"], data["height"])
    else:
        raise ValueError("Unknown shape type")

# Register for base class
kajson.UniversalJSONDecoder.register(Shape, decode_shape)
```

## Integration with Pydantic

### Custom Pydantic Decoding

```python
from pydantic import BaseModel, ValidationError

class StrictUser(BaseModel):
    name: str
    age: int
    
    @classmethod
    def __json_decode__(cls, data: dict) -> "StrictUser":
        """Custom decoding with extra validation"""
        # Pre-process data
        if "age" in data and data["age"] < 0:
            data["age"] = 0  # Fix negative ages
        
        try:
            return cls(**data)
        except ValidationError as e:
            # Custom error handling
            raise KajsonDecoderError(f"Invalid user data: {e}")
```

## Error Handling in Decoders

### Comprehensive Error Handling

```python
def robust_decode(data: Dict[str, Any]) -> Any:
    """Decoder with comprehensive error handling"""
    try:
        # Check for required fields
        if "__type__" not in data:
            raise ValueError("Missing type information")
        
        type_name = data["__type__"]
        
        # Validate type
        if type_name not in ALLOWED_TYPES:
            raise ValueError(f"Unknown type: {type_name}")
        
        # Reconstruct object
        obj_class = ALLOWED_TYPES[type_name]
        return obj_class(**data.get("fields", {}))
        
    except KeyError as e:
        raise KajsonDecoderError(f"Missing required field: {e}")
    except TypeError as e:
        raise KajsonDecoderError(f"Type error during reconstruction: {e}")
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected decoding error: {e}")
        raise KajsonDecoderError(f"Failed to decode object: {e}")
```

### Decoder with Logging

```python
import logging

logger = logging.getLogger(__name__)

def logged_decode(data: Dict[str, Any]) -> Any:
    """Decoder that logs all operations"""
    logger.debug(f"Decoding data: {data}")
    
    try:
        result = perform_decode(data)
        logger.debug(f"Successfully decoded: {type(result).__name__}")
        return result
    except Exception as e:
        logger.error(f"Decoding failed: {e}", exc_info=True)
        raise
```

## Performance Optimization

### Cached Decoders

```python
from functools import lru_cache

@lru_cache(maxsize=256)
def get_decoder_for_type(type_name: str) -> Optional[Callable]:
    """Cache decoder lookups for performance"""
    for type_class, decoder in kajson.UniversalJSONDecoder._decoders.items():
        if type_class.__name__ == type_name:
            return decoder
    return None
```

### Batch Decoding

```python
def decode_batch(json_strings: List[str]) -> List[Any]:
    """Efficiently decode multiple JSON strings"""
    results = []
    errors = []
    
    for i, json_str in enumerate(json_strings):
        try:
            results.append(kajson.loads(json_str))
        except Exception as e:
            errors.append((i, str(e)))
    
    if errors:
        logger.warning(f"Failed to decode {len(errors)} items")
    
    return results
```

## See Also

- [Encoder API](encoder.md) - Corresponding encoder documentation
- [kajson Module API](kajson.md) - Main module functions
- [Error Handling Guide](../guide/error-handling.md) - Handling decoder errors
