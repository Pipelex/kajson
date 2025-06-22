# Encoder API Reference

The encoder module provides classes and utilities for serializing Python objects to JSON with extended type support.

## UniversalJSONEncoder

The main encoder class that extends `json.JSONEncoder` to handle additional Python types.

### Class Definition

```python
class UniversalJSONEncoder(json.JSONEncoder):
    """Enhanced JSON encoder with support for custom types"""
```

### Constructor

```python
def __init__(
    self,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = False,
    check_circular: bool = True,
    allow_nan: bool = True,
    sort_keys: bool = False,
    indent: int | str | None = None,
    separators: tuple[str, str] | None = None,
    default: Callable[[Any], Any] | None = None
) -> None
```

**Parameters:** Same as `json.JSONEncoder`

### Methods

#### default

```python
def default(self, obj: Any) -> Any
```

Override this method to provide custom serialization for objects that the standard encoder cannot handle.

**Parameters:**
- `obj`: Object to encode

**Returns:** JSON-serializable representation of the object

**Example:**

```python
class MyEncoder(kajson.UniversalJSONEncoder):
    def default(self, obj):
        if isinstance(obj, MyCustomClass):
            return {"custom": obj.to_dict()}
        return super().default(obj)
```

### Class Methods

#### register

```python
@classmethod
def register(
    cls,
    type_class: Type,
    encoder: Callable[[Any], dict]
) -> None
```

Register a custom encoder function for a specific type.

**Parameters:**
- `type_class`: The Python type to register
- `encoder`: Function that converts instances of `type_class` to a dict

**Example:**

```python
from decimal import Decimal

def encode_decimal(value: Decimal) -> dict:
    return {
        "__decimal__": str(value),
        "precision": value.as_tuple().exponent
    }

kajson.UniversalJSONEncoder.register(Decimal, encode_decimal)
```

#### unregister

```python
@classmethod
def unregister(cls, type_class: Type) -> None
```

Remove a previously registered encoder for a type.

**Parameters:**
- `type_class`: The type to unregister

#### get_registered_types

```python
@classmethod
def get_registered_types(cls) -> List[Type]
```

Get a list of all registered types.

**Returns:** List of types with custom encoders

## Built-in Encoders

Kajson includes built-in encoders for common types:

### DateTime Encoder

```python
def encode_datetime(dt: datetime) -> dict:
    """Encode datetime objects"""
    return {
        "__datetime__": dt.isoformat(),
        "tzinfo": dt.tzinfo.tzname() if dt.tzinfo else None
    }
```

### Date Encoder

```python
def encode_date(d: date) -> dict:
    """Encode date objects"""
    return {"__date__": d.isoformat()}
```

### Time Encoder

```python
def encode_time(t: time) -> dict:
    """Encode time objects"""
    return {
        "__time__": t.isoformat(),
        "tzinfo": t.tzinfo.tzname() if t.tzinfo else None
    }
```

### Timedelta Encoder

```python
def encode_timedelta(td: timedelta) -> dict:
    """Encode timedelta objects"""
    return {
        "__timedelta__": {
            "days": td.days,
            "seconds": td.seconds,
            "microseconds": td.microseconds
        }
    }
```

### Timezone Encoder

```python
def encode_timezone(tz: timezone) -> dict:
    """Encode timezone objects"""
    return {
        "__timezone__": {
            "offset": tz.utcoffset(None).total_seconds(),
            "name": tz.tzname(None)
        }
    }
```

## Custom Encoder Implementation

### Basic Custom Encoder

```python
import kajson
from typing import Any, Dict

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

def encode_point(point: Point) -> Dict[str, Any]:
    return {
        "__point__": True,
        "x": point.x,
        "y": point.y
    }

# Register the encoder
kajson.UniversalJSONEncoder.register(Point, encode_point)

# Now Point objects can be serialized
p = Point(3.14, 2.71)
json_str = kajson.dumps(p)
```

### Encoder with Validation

```python
def encode_positive_int(value: int) -> Dict[str, Any]:
    if value <= 0:
        raise ValueError(f"Expected positive integer, got {value}")
    return {"__positive_int__": value}

class PositiveInt:
    def __init__(self, value: int):
        if value <= 0:
            raise ValueError("Must be positive")
        self.value = value

kajson.UniversalJSONEncoder.register(PositiveInt, 
    lambda pi: encode_positive_int(pi.value))
```

### Conditional Encoding

```python
import os

def encode_path(path: Path) -> Dict[str, Any]:
    """Encode path with additional metadata"""
    result = {"__path__": str(path)}
    
    # Add metadata if path exists
    if path.exists():
        result.update({
            "exists": True,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size": path.stat().st_size if path.is_file() else None
        })
    else:
        result["exists"] = False
    
    return result
```

## Advanced Encoding Patterns

### Recursive Type Encoding

```python
from typing import List, Optional

class TreeNode:
    def __init__(self, value: Any, children: Optional[List["TreeNode"]] = None):
        self.value = value
        self.children = children or []

def encode_tree_node(node: TreeNode) -> Dict[str, Any]:
    return {
        "__tree_node__": True,
        "value": node.value,
        "children": node.children  # Recursively encoded
    }

kajson.UniversalJSONEncoder.register(TreeNode, encode_tree_node)

# Create tree
root = TreeNode("root", [
    TreeNode("child1", [TreeNode("grandchild1")]),
    TreeNode("child2")
])

# Serialize entire tree
json_str = kajson.dumps(root)
```

### Encoder with Type Hints

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Box(Generic[T]):
    def __init__(self, value: T):
        self.value = value
        self.type_name = type(value).__name__

def encode_box(box: Box) -> Dict[str, Any]:
    return {
        "__box__": True,
        "value": box.value,
        "type_hint": box.type_name
    }

kajson.UniversalJSONEncoder.register(Box, encode_box)
```

## Performance Considerations

### Caching Encoders

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_encoder_for_type(type_class: Type) -> Optional[Callable]:
    """Cache encoder lookups for performance"""
    return kajson.UniversalJSONEncoder._encoders.get(type_class)
```

### Bulk Registration

```python
# Register multiple types at once
encoders = {
    IPv4Address: lambda ip: {"__ipv4__": str(ip)},
    IPv6Address: lambda ip: {"__ipv6__": str(ip)},
    UUID: lambda u: {"__uuid__": str(u)},
    Path: lambda p: {"__path__": str(p)}
}

for type_class, encoder in encoders.items():
    kajson.UniversalJSONEncoder.register(type_class, encoder)
```

## Error Handling in Encoders

### Safe Encoding Pattern

```python
def safe_encode(value: Any) -> Dict[str, Any]:
    """Encoder with comprehensive error handling"""
    try:
        # Validate input
        if value is None:
            return {"__null__": True}
        
        # Perform encoding
        result = {
            "__type__": type(value).__name__,
            "data": str(value)
        }
        
        # Validate output
        if not isinstance(result, dict):
            raise TypeError("Encoder must return a dict")
        
        return result
        
    except Exception as e:
        # Log error and re-raise
        print(f"Encoding error for {type(value)}: {e}")
        raise
```

## Integration with Pydantic

Kajson automatically handles Pydantic models, but you can customize the encoding:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    internal_field: str = "secret"
    
    def __json_encode__(self) -> dict:
        """Custom encoding that excludes internal fields"""
        data = self.model_dump()
        data.pop('internal_field', None)
        return data
```

## See Also

- [Decoder API](decoder.md) - Corresponding decoder documentation
- [kajson Module API](kajson.md) - Main module functions
- [Custom Types Guide](../guide/custom-types.md) - Tutorial on adding custom types 