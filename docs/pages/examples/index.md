# Examples

This section contains practical examples demonstrating how to use Kajson. All examples are available as executable files in the [`examples/`](https://github.com/PipelexLab/kajson/tree/main/examples) directory.

## Basic Pydantic Model Serialization

**Source:** [`ex_01_basic_pydantic_serialization.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_01_basic_pydantic_serialization.py)

Shows how to serialize and deserialize Pydantic models with datetime fields - no special handling required.

```python
from datetime import datetime
from pydantic import BaseModel
from kajson import kajson, kajson_manager

class User(BaseModel):
    name: str
    email: str
    created_at: datetime

def main():
    # Create and serialize
    user = User(
        name="Alice",
        email="alice@example.com",
        created_at=datetime.now()
    )

    # Serialize to JSON
    json_str = kajson.dumps(user, indent=2)

    # Deserialize back
    restored_user = kajson.loads(json_str)
    assert user == restored_user  # ✅ Perfect reconstruction!

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

## Nested Models with Mixed Types

**Source:** [`ex_02_nested_models_mixed_types.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_02_nested_models_mixed_types.py)

Demonstrates handling complex nested structures with multiple Pydantic models, lists, datetime and timedelta types.

```python
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel
from kajson import kajson, kajson_manager

class Comment(BaseModel):
    author: str
    text: str
    posted_at: datetime

class BlogPost(BaseModel):
    title: str
    content: str
    published_at: datetime
    read_time: timedelta
    comments: List[Comment]

def main():
    # Create complex nested structure
    post = BlogPost(
        title="Kajson Makes JSON Easy",
        content="No more 'not JSON serializable' errors!",
        published_at=datetime.now(),
        read_time=timedelta(minutes=5),
        comments=[
            Comment(author="Bob", text="Great post!", posted_at=datetime.now()),
            Comment(author="Carol", text="Very helpful", posted_at=datetime.now())
        ]
    )

    # Works seamlessly!
    json_str = kajson.dumps(post)
    restored = kajson.loads(json_str)
    assert post == restored

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

## Custom Classes with JSON Hooks

**Source:** [`ex_03_custom_classes_json_hooks.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_03_custom_classes_json_hooks.py)

Shows how to implement `__json_encode__` and `__json_decode__` methods for custom serialization behavior.

```python
from typing import Any, Dict
from typing_extensions import override
from kajson import kajson, kajson_manager

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __json_encode__(self):
        """Called during serialization"""
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def __json_decode__(cls, data: Dict[str, Any]):
        """Called during deserialization"""
        return cls(data["x"], data["y"])
    
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y

    @override
    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"

def main():
    # Use it directly
    point = Point(3.14, 2.71)
    json_str = kajson.dumps(point)
    restored = kajson.loads(json_str)
    assert point == restored

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

## Registering Custom Type Encoders

**Source:** [`ex_04_registering_custom_encoders.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_04_registering_custom_encoders.py)

Demonstrates how to register custom encoders and decoders for types like `Decimal` and `Path`.

```python
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict
from kajson import kajson, kajson_manager

def main():
    # Register Decimal support
    kajson.UniversalJSONEncoder.register(
        Decimal,
        lambda d: {"decimal": str(d)}
    )
    kajson.UniversalJSONDecoder.register(
        Decimal,
        lambda data: Decimal(data["decimal"])
    )

    # Register Path support - handle both abstract and concrete types
    def encode_path(p: Path) -> Dict[str, Any]:
        return {"path": str(p)}

    def decode_path(data: Dict[str, Any]) -> Path:
        return Path(data["path"])

    kajson.UniversalJSONEncoder.register(Path, encode_path)
    kajson.UniversalJSONDecoder.register(Path, decode_path)

    # Also register for the concrete Path type (PosixPath/WindowsPath)
    concrete_path_type = type(Path())
    if concrete_path_type != Path:
        kajson.UniversalJSONEncoder.register(concrete_path_type, encode_path)
        kajson.UniversalJSONDecoder.register(concrete_path_type, decode_path)

    # Now they work!
    data = {
        "price": Decimal("19.99"),
        "config_path": Path("/etc/app/config.json")
    }
    restored = kajson.loads(kajson.dumps(data))
    assert restored["price"] == Decimal("19.99")
    assert isinstance(restored["config_path"], Path)

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

## Working with Lists of Mixed Types

**Source:** [`ex_05_mixed_types_lists.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_05_mixed_types_lists.py)

Shows how Kajson handles heterogeneous lists containing different object types seamlessly.

```python
from datetime import date, datetime, time
from pydantic import BaseModel
from kajson import kajson, kajson_manager

class Task(BaseModel):
    name: str
    due_date: date

def main():
    # Mix different types in one list
    mixed_data = [
        Task(name="Review PR", due_date=date.today()),
        datetime.now(),
        {"plain": "dict"},
        ["plain", "list"],
        time(14, 30),
    ]

    # Kajson handles everything
    json_str = kajson.dumps(mixed_data)
    restored = kajson.loads(json_str)

    # Types are preserved
    assert isinstance(restored[0], Task)
    assert isinstance(restored[1], datetime)
    assert isinstance(restored[4], time)

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

## Error Handling with Validation

**Source:** [`ex_06_error_handling_validation.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_06_error_handling_validation.py)

Demonstrates proper error handling when Pydantic validation fails during deserialization.

```python
from pydantic import BaseModel, Field
from kajson import kajson, kajson_manager

class Product(BaseModel):
    name: str
    price: float = Field(gt=0)  # Must be positive

def main():
    # Valid data works fine
    product = Product(name="Widget", price=19.99)
    json_str = kajson.dumps(product)
    restored = kajson.loads(json_str)

    # Invalid data in JSON
    invalid_json = '''
{
    "name": "Widget",
    "price": -10,
    "__class__": "Product",
    "__module__": "__main__"
}
'''

    try:
        kajson.loads(invalid_json)
    except kajson.KajsonDecoderError:
        print("✅ Validation failed as expected!")
        # Kajson properly caught the Pydantic validation error

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

## Drop-in Replacement Usage

**Source:** [`ex_07_drop_in_replacement.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_07_drop_in_replacement.py)

Shows how to use Kajson as a direct replacement for Python's standard `json` module.

```python
# Simply change your import
import kajson as json  # Instead of: import json
from datetime import datetime
from kajson import kajson_manager

def main():
    # All your existing code works!
    data = {"user": "Alice", "logged_in": datetime.now()}
    json_str = json.dumps(data)  # Works with datetime!
    restored = json.loads(json_str)

    # Or use kajson directly
    import kajson
    json_str2 = kajson.dumps(data)
    restored2 = kajson.loads(json_str2)

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

## Additional Examples

The [`examples/`](https://github.com/PipelexLab/kajson/tree/main/examples) directory contains additional examples:

- **README Examples** (`ex_08_readme_basic_usage.py` - `ex_13_readme_error_handling.py`): Examples used in the project README with detailed explanations and comparisons with standard JSON
- **Complex Nested Models** (`ex_09_readme_complex_nested.py`): More complex nesting scenarios with metadata
- **Advanced Custom Registration** (`ex_10_readme_custom_registration.py`): Detailed custom type registration examples
- **Custom Hooks Variations** (`ex_11_readme_custom_hooks.py`): Alternative implementations of custom JSON hooks

## Running the Examples

To run any example:

```bash
cd examples
python ex_01_basic_pydantic_serialization.py
```

All examples are self-contained and demonstrate different aspects of Kajson's capabilities. Each file includes detailed comments explaining the concepts being demonstrated.
