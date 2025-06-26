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

## Pydantic Subclass Polymorphism

**Source:** [`ex_15_pydantic_subclass_polymorphism.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_15_pydantic_subclass_polymorphism.py)

Demonstrates Kajson's powerful ability to preserve exact subclass types during serialization, even when fields are declared with base class types. This is perfect for polymorphic APIs, plugin architectures, and complex data modeling.

```python
from typing import List
from typing_extensions import override
from pydantic import BaseModel, Field
from kajson import kajson, kajson_manager

class Animal(BaseModel):
    """Base animal class with common attributes."""
    name: str
    species: str
    age: int

    def make_sound(self) -> str:
        return "Some generic animal sound"

class Dog(Animal):
    """Dog subclass with breed-specific attributes."""
    breed: str
    is_good_boy: bool = True
    favorite_toy: str = "tennis ball"

    @override
    def make_sound(self) -> str:
        return "Woof! Woof!"

class Cat(Animal):
    """Cat subclass with feline-specific attributes."""
    lives_remaining: int = 9
    is_indoor: bool = True
    favorite_nap_spot: str = "sunny windowsill"

    @override
    def make_sound(self) -> str:
        return "Meow~"

class Pet(BaseModel):
    """Pet registration with owner information."""
    owner_name: str
    animal: Animal  # ← Field declared as base class, but can hold subclass instances
    registration_date: str
    veterinarian: str

class AnimalShelter(BaseModel):
    """Animal shelter with mixed animal types."""
    name: str
    location: str
    animals: List[Animal]  # ← List of base class, but can contain subclass instances
    capacity: int

def main():
    # Create pets with different animal subclasses
    pets = [
        Pet(
            owner_name="Alice Smith",
            animal=Dog(name="Buddy", species="Canis lupus", age=3, breed="Golden Retriever"),
            registration_date="2024-01-15",
            veterinarian="Dr. Johnson"
        ),
        Pet(
            owner_name="Bob Wilson",
            animal=Cat(name="Whiskers", species="Felis catus", age=5, lives_remaining=8),
            registration_date="2024-02-20",
            veterinarian="Dr. Martinez"
        )
    ]

    # Create shelter with mixed types
    shelter = AnimalShelter(
        name="Happy Paws Animal Shelter",
        location="Springfield",
        capacity=50,
        animals=[
            Dog(name="Max", species="Canis lupus", age=4, breed="German Shepherd"),
            Cat(name="Luna", species="Felis catus", age=2, lives_remaining=9),
        ]
    )

    # Serialize everything
    pets_json = kajson.dumps(pets, indent=2)
    shelter_json = kajson.dumps(shelter, indent=2)

    # Deserialize and verify subclass types are preserved
    restored_pets = kajson.loads(pets_json)
    restored_shelter = kajson.loads(shelter_json)

    # Subclass types and attributes are perfectly preserved!
    assert isinstance(restored_pets[0].animal, Dog)  # Still a Dog, not just Animal
    assert restored_pets[0].animal.breed == "Golden Retriever"  # Subclass attributes intact
    assert restored_pets[0].animal.make_sound() == "Woof! Woof!"  # Subclass methods work

    assert isinstance(restored_pets[1].animal, Cat)  # Still a Cat
    assert restored_pets[1].animal.lives_remaining == 8  # Cat-specific attributes preserved
    assert restored_pets[1].animal.make_sound() == "Meow~"  # Cat methods work

    print("🎉 Subclass polymorphism works perfectly!")

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

**Key Benefits:**
- **🎭 Polymorphic APIs** - Base class endpoints that handle multiple subclasses
- **🗂️ Mixed collections** - Lists of base class containing various subclasses  
- **🏗️ Plugin architectures** - Runtime-loaded implementations of base interfaces
- **📊 Data modeling** - Complex hierarchies with specialized behaviors

## Generic Pydantic Models

**Source:** [`ex_16_generic_models.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_16_generic_models.py)

Demonstrates comprehensive support for generic Pydantic models with type parameters. Perfect for type-safe containers, APIs, and data structures that need parametric polymorphism.

```python
from typing import Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel
from kajson import kajson, kajson_manager

T = TypeVar("T")
K = TypeVar("K") 
V = TypeVar("V")

class Container(BaseModel, Generic[T]):
    """A generic container that can hold any type safely."""
    name: str
    items: List[T]
    capacity: int

class KeyValueStore(BaseModel, Generic[K, V]):
    """A generic key-value store with typed keys and values."""
    name: str
    data: Dict[K, V]
    created_by: str

class ApiResponse(BaseModel, Generic[T]):
    """A generic API response wrapper."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: str

def main():
    # Single type parameter
    string_container = Container[str](
        name="fruits",
        items=["apple", "banana", "cherry"],
        capacity=10
    )
    
    # Multiple type parameters
    scores = KeyValueStore[str, int](
        name="user_scores",
        data={"alice": 95, "bob": 87},
        created_by="admin"
    )
    
    # Nested generics
    response = ApiResponse[List[Product]](
        success=True,
        data=[Product(name="Widget", price=19.99)],
        timestamp="2025-01-15T10:30:00Z"
    )
    
    # All serialize and deserialize perfectly!
    containers_json = kajson.dumps([string_container, scores, response])
    restored = kajson.loads(containers_json)
    
    # Type information is preserved
    assert isinstance(restored[0], Container)  # Container[str]
    assert isinstance(restored[1], KeyValueStore)  # KeyValueStore[str, int]
    assert isinstance(restored[2], ApiResponse)  # ApiResponse[List[Product]]

if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
```

**Key Features:**
- **🏗️ Single type parameters** - `Container[T]` for type-safe collections
- **⚙️ Multiple parameters** - `KeyValueStore[K, V]` for complex relationships
- **🔗 Nested generics** - `ApiResponse[List[Product]]` for API patterns
- **🎯 Bounded types** - `Calculator[NumericType]` with type constraints
- **✨ Perfect preservation** - All type information maintained during roundtrip

## Dynamic Class Registry

**Source:** [`ex_14_dynamic_class_registry.py`](https://github.com/PipelexLab/kajson/blob/main/examples/ex_14_dynamic_class_registry.py)

Shows when and how to use the class registry for dynamically created classes that aren't available in standard module paths. Essential for distributed systems and runtime class generation.

```python
from kajson import kajson, kajson_manager
from kajson.kajson_manager import KajsonManager

def main():
    # Simulate dynamic class creation (e.g., from network, workflow definition)
    remote_class_definition = '''
from pydantic import BaseModel, Field

class RemoteTask(BaseModel):
    task_id: str
    name: str  
    priority: int = Field(default=1, ge=1, le=10)
'''

    # Execute and create the class dynamically
    remote_namespace = {}
    exec(remote_class_definition, remote_namespace)
    RemoteTask = remote_namespace["RemoteTask"]

    # Set module to simulate it's not available locally
    RemoteTask.__module__ = "remote.distributed.system"

    # Create and serialize
    task = RemoteTask(task_id="TASK_001", name="Process Data", priority=5)
    json_str = kajson.dumps(task)

    # Clear local definition (simulate distributed scenario)
    del remote_namespace["RemoteTask"]

    # Register in class registry for deserialization
    registry = KajsonManager.get_class_registry()
    registry.register_class(RemoteTask)

    # Now deserialization works via class registry!
    restored_task = kajson.loads(json_str)
    assert restored_task.task_id == "TASK_001"

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
