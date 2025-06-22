# kajson Module API Reference

The main `kajson` module provides drop-in replacement functions for Python's standard `json` module with enhanced type support.

## Core Functions

### dumps

```python
def dumps(
    obj: Any,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = False,
    check_circular: bool = True,
    allow_nan: bool = True,
    cls: Type[JSONEncoder] | None = None,
    indent: int | str | None = None,
    separators: tuple[str, str] | None = None,
    default: Callable[[Any], Any] | None = None,
    sort_keys: bool = False,
    **kw: Any
) -> str
```

Serialize `obj` to a JSON formatted string using the enhanced encoder.

**Parameters:**

- `obj`: The Python object to serialize
- `skipkeys`: If True, skip keys that are not basic types (default: False)
- `ensure_ascii`: If True, escape all non-ASCII characters (default: False)
- `check_circular`: If False, skip circular reference check (default: True)
- `allow_nan`: If True, allow NaN, Infinity, -Infinity (default: True)
- `cls`: Custom encoder class (default: UniversalJSONEncoder)
- `indent`: Number of spaces for indentation, or None for compact output
- `separators`: Tuple of (item_separator, key_separator)
- `default`: Function called for objects that can't be serialized
- `sort_keys`: If True, sort dictionary keys (default: False)
- `**kw`: Additional keyword arguments passed to the encoder

**Returns:** JSON string representation of the object

**Example:**

```python
import kajson
from datetime import datetime

data = {
    "name": "Alice",
    "created_at": datetime.now(),
    "active": True
}

json_str = kajson.dumps(data, indent=2)
print(json_str)
```

### loads

```python
def loads(
    s: str | bytes | bytearray,
    *,
    cls: Type[JSONDecoder] | None = None,
    object_hook: Callable[[dict[str, Any]], Any] | None = None,
    parse_float: Callable[[str], Any] | None = None,
    parse_int: Callable[[str], Any] | None = None,
    parse_constant: Callable[[str], Any] | None = None,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None,
    **kw: Any
) -> Any
```

Deserialize a JSON string to a Python object with type reconstruction.

**Parameters:**

- `s`: JSON string, bytes, or bytearray to deserialize
- `cls`: Custom decoder class (default: UniversalJSONDecoder)
- `object_hook`: Function called with every JSON object decoded
- `parse_float`: Function to parse float values
- `parse_int`: Function to parse integer values
- `parse_constant`: Function to parse constants (NaN, Infinity, -Infinity)
- `object_pairs_hook`: Function called with ordered list of pairs
- `**kw`: Additional keyword arguments passed to the decoder

**Returns:** Deserialized Python object

**Raises:**
- `JSONDecodeError`: If the JSON syntax is invalid
- `KajsonDecoderError`: If type reconstruction fails

**Example:**

```python
import kajson

json_str = '{"name": "Alice", "age": 30}'
data = kajson.loads(json_str)
print(data)  # {'name': 'Alice', 'age': 30}
```

### dump

```python
def dump(
    obj: Any,
    fp: IO[str],
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = False,
    check_circular: bool = True,
    allow_nan: bool = True,
    cls: Type[JSONEncoder] | None = None,
    indent: int | str | None = None,
    separators: tuple[str, str] | None = None,
    default: Callable[[Any], Any] | None = None,
    sort_keys: bool = False,
    **kw: Any
) -> None
```

Serialize `obj` to a JSON formatted stream.

**Parameters:**

- `obj`: The Python object to serialize
- `fp`: File-like object supporting `.write()`
- Other parameters: Same as `dumps()`

**Example:**

```python
import kajson
from datetime import date

data = {
    "event": "Conference",
    "date": date(2025, 3, 15),
    "attendees": 150
}

with open("event.json", "w") as f:
    kajson.dump(data, f, indent=2)
```

### load

```python
def load(
    fp: IO[str] | IO[bytes],
    *,
    cls: Type[JSONDecoder] | None = None,
    object_hook: Callable[[dict[str, Any]], Any] | None = None,
    parse_float: Callable[[str], Any] | None = None,
    parse_int: Callable[[str], Any] | None = None,
    parse_constant: Callable[[str], Any] | None = None,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None,
    **kw: Any
) -> Any
```

Deserialize a JSON file to a Python object.

**Parameters:**

- `fp`: File-like object supporting `.read()`
- Other parameters: Same as `loads()`

**Returns:** Deserialized Python object

**Example:**

```python
import kajson

with open("data.json", "r") as f:
    data = kajson.load(f)
```

## Special Classes

### UniversalJSONEncoder

The default encoder class that handles extended types. Can be subclassed for custom behavior.

**Class Methods:**

```python
@classmethod
def register(cls, type_class: Type, encoder: Callable[[Any], dict]) -> None
```

Register a custom encoder for a specific type.

**Example:**

```python
from decimal import Decimal

def encode_decimal(d: Decimal) -> dict:
    return {"__decimal__": str(d)}

kajson.UniversalJSONEncoder.register(Decimal, encode_decimal)
```

### UniversalJSONDecoder

The default decoder class that reconstructs original types. Can be subclassed for custom behavior.

**Class Methods:**

```python
@classmethod
def register(cls, type_class: Type, decoder: Callable[[dict], Any]) -> None
```

Register a custom decoder for a specific type.

**Example:**

```python
from decimal import Decimal

def decode_decimal(data: dict) -> Decimal:
    return Decimal(data["__decimal__"])

kajson.UniversalJSONDecoder.register(Decimal, decode_decimal)
```

## Exceptions

### JSONDecodeError

Standard JSON syntax error, inherited from `json.JSONDecodeError`.

**Attributes:**
- `msg`: Error message
- `doc`: JSON document being parsed
- `pos`: Position where error occurred

### KajsonDecoderError

Raised when type reconstruction fails during deserialization.

**Example:**

```python
try:
    kajson.loads(invalid_json)
except kajson.JSONDecodeError as e:
    print(f"Invalid JSON at position {e.pos}: {e.msg}")
except kajson.KajsonDecoderError as e:
    print(f"Type reconstruction failed: {e}")
```

## Type Support

### Built-in Type Support

Kajson automatically handles these types without configuration:

- All standard JSON types (dict, list, str, int, float, bool, None)
- `datetime.datetime`
- `datetime.date`
- `datetime.time`
- `datetime.timedelta`
- `datetime.timezone`
- Pydantic BaseModel (v2)
- Classes with `__json_encode__` and `__json_decode__` methods

### Custom Type Hooks

Classes can implement these methods for automatic serialization:

```python
class MyClass:
    def __json_encode__(self) -> dict:
        """Return dict representation for JSON encoding"""
        return {"data": self.data}
    
    @classmethod
    def __json_decode__(cls, data: dict) -> "MyClass":
        """Reconstruct instance from dict"""
        return cls(data["data"])
```

## Complete Example

```python
import kajson
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List

class Task(BaseModel):
    id: int
    title: str
    due_date: datetime
    estimated_time: timedelta
    tags: List[str]

# Create tasks
tasks = [
    Task(
        id=1,
        title="Write documentation",
        due_date=datetime(2025, 2, 1, 17, 0),
        estimated_time=timedelta(hours=3),
        tags=["docs", "priority"]
    ),
    Task(
        id=2,
        title="Review PRs",
        due_date=datetime(2025, 2, 2, 10, 0),
        estimated_time=timedelta(hours=1, minutes=30),
        tags=["review", "team"]
    )
]

# Serialize to JSON
json_str = kajson.dumps(tasks, indent=2)
print("Serialized:", json_str)

# Save to file
with open("tasks.json", "w") as f:
    kajson.dump(tasks, f, indent=2)

# Load from file
with open("tasks.json", "r") as f:
    loaded_tasks = kajson.load(f)

# Verify types are preserved
for task in loaded_tasks:
    assert isinstance(task, Task)
    assert isinstance(task.due_date, datetime)
    assert isinstance(task.estimated_time, timedelta)

print(f"Successfully loaded {len(loaded_tasks)} tasks")
```

## See Also

- [Encoder API](encoder.md) - Detailed encoder documentation
- [Decoder API](decoder.md) - Detailed decoder documentation
- [Custom Types Guide](../guide/custom-types.md) - How to add custom type support 