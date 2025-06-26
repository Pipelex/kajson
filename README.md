# 🚀 Kajson - Universal JSON Encoder/Decoder for Python

[![PyPI version](https://img.shields.io/pypi/v/kajson.svg)](https://pypi.org/project/kajson/)
[![Python versions](https://img.shields.io/pypi/pyversions/kajson.svg)](https://pypi.org/project/kajson/)
[![License](https://img.shields.io/pypi/l/kajson.svg)](https://github.com/Pipelex/kajson/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-kajson-blue)](https://pipelex.github.io/kajson)
[![Discord](https://img.shields.io/badge/Discord-5865F2?logo=discord&logoColor=white)](https://go.pipelex.com/discord)
[![Website](https://img.shields.io/badge/Pipelex-03bb95?logo=google-chrome&logoColor=white&style=flat)](https://pipelex.com)


**Kajson** is a powerful drop-in replacement for Python's standard `json` module that automatically handles complex object serialization, including **Pydantic v2 models**, **datetime objects**, and **custom types**.

This library is used by [Pipelex](https://github.com/Pipelex/pipelex), the open-source language for repeatable AI workflows, [check it out](https://github.com/Pipelex/pipelex).

## ✨ Why Kajson?

Say goodbye to `type X is not JSON serializable`!

### The Problem with Standard JSON

```python
import json
from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    name: str
    created_at: datetime

user = User(name="Alice", created_at=datetime.now())

# ❌ Standard json fails
json.dumps(user)  # TypeError: Object of type User is not JSON serializable
```

### The Kajson Solution

**Full example:** [`ex_08_readme_basic_usage.py`](examples/ex_08_readme_basic_usage.py)

```python
import kajson

# ✅ Just works!
json_str = kajson.dumps(user)
restored_user = kajson.loads(json_str)
assert user == restored_user  # Perfect reconstruction!
```

## 🎯 Key Features

- **🔄 Drop-in replacement** - Same API as standard `json` module
- **🐍 Pydantic v2 support** - Seamless serialization of Pydantic models
- **📅 DateTime handling** - Built-in support for date, time, datetime, timedelta
- **🏗️ Type preservation** - Automatically preserves and reconstructs original types
- **🏛️ Class registry** - Handle dynamic classes from distributed systems and runtime generation
- **🔌 Extensible** - Easy registration of custom encoders/decoders
- **🎁 Batteries included** - Common types work out of the box

## 📦 Installation

```bash
# Using pip
pip install kajson

# Using poetry
poetry add kajson

# Using uv (recommended)
uv pip install kajson
```

## 🚀 Quick Start

### Basic Usage

**Full example:** [`ex_01_basic_pydantic_serialization.py`](examples/ex_01_basic_pydantic_serialization.py)

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

### Working with Complex Nested Models

**Full example:** [`ex_09_readme_complex_nested.py`](examples/ex_09_readme_complex_nested.py)

```python
from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel

class Comment(BaseModel):
    author: str
    content: str
    created_at: datetime

class BlogPost(BaseModel):
    title: str
    content: str
    published_at: datetime
    comments: List[Comment]
    metadata: Dict[str, Any]

# Create complex nested structure
post = BlogPost(
    title="Introducing Kajson",
    content="A powerful JSON library...",
    published_at=datetime.now(),
    comments=[
        Comment(author="Alice", content="Great post!", created_at=datetime.now()),
        Comment(author="Bob", content="Very helpful", created_at=datetime.now())
    ],
    metadata={"views": 1000, "likes": 50}
)

# Serialize and deserialize - it just works!
json_str = kajson.dumps(post)
restored_post = kajson.loads(json_str)

# All nested objects are perfectly preserved
assert isinstance(restored_post.comments[0], Comment)
assert restored_post.comments[0].created_at.year == datetime.now().year
```

## 🤝 Compatibility

- **Python**: 3.9+
- **Pydantic**: v2.x
- **Dependencies**: Minimal, only standard library + pydantic

## 🔄 Migration from Standard JSON

Migrating is as simple as changing your import:

```python
# Before
import json
data = json.dumps(my_object)  # Often fails with complex objects

# After  
import kajson as json  # Drop-in replacement!
data = json.dumps(my_object)  # Works with complex objects
```

Or use Kajson's convenience functions directly:

```python
import kajson
data = kajson.dumps(my_object)
```

## 🏗️ How It Works

Kajson extends the standard JSON encoder/decoder by:

1. **Type Preservation**: Adds `__class__` and `__module__` metadata to JSON objects
2. **Smart Decoding**: Automatically reconstructs original Python objects
3. **Registry System**: Allows registration of custom encoders/decoders
4. **Pydantic Integration**: Special handling for Pydantic models and validation
5. **Class Registry**: Maintains a registry of dynamically created classes that aren't available in standard module paths, enabling serialization/deserialization in distributed systems and runtime scenarios

## 📚 Use Cases

- **REST APIs**: Serialize Pydantic models for API responses
- **Data Persistence**: Save complex objects to JSON files
- **Message Queues**: Send rich objects through Redis/RabbitMQ
- **Configuration**: Store config with proper types
- **Data Science**: Serialize numpy arrays, pandas DataFrames (with custom encoders)


## 🔧 Advanced Features

### Custom Type Registration

**Full example:** [`ex_10_readme_custom_registration.py`](examples/ex_10_readme_custom_registration.py)

Register encoders/decoders for any type:

```python
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict
import kajson

# Register Decimal support
def encode_decimal(value: Decimal) -> Dict[str, str]:
    return {"decimal": str(value)}

def decode_decimal(data: Dict[str, str]) -> Decimal:
    return Decimal(data["decimal"])

kajson.UniversalJSONEncoder.register(Decimal, encode_decimal)
kajson.UniversalJSONDecoder.register(Decimal, decode_decimal)

# Now Decimal works seamlessly
data = {"price": Decimal("19.99"), "tax": Decimal("1.50")}
json_str = kajson.dumps(data)
restored = kajson.loads(json_str)
assert restored["price"] == Decimal("19.99")  # ✅

# Register Path support
kajson.UniversalJSONEncoder.register(
    Path, 
    lambda p: {"path": str(p)}
)
kajson.UniversalJSONDecoder.register(
    Path, 
    lambda d: Path(d["path"])
)

# Path objects now work too!
config = {"home": Path.home(), "config": Path("/etc/myapp/config.json")}
restored_config = kajson.loads(kajson.dumps(config))
```

### Custom Classes with Hooks

**Full example:** [`ex_11_readme_custom_hooks.py`](examples/ex_11_readme_custom_hooks.py)

Add JSON support to your own classes:

```python
from typing import Any, Dict
from typing_extensions import override

class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __json_encode__(self):
        """Called by Kajson during serialization"""
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def __json_decode__(cls, data: Dict[str, Any]):
        """Called by Kajson during deserialization"""
        return cls(data["x"], data["y"])
    
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return self.x == other.x and self.y == other.y

# Works automatically!
vector = Vector(3.14, 2.71)
restored = kajson.loads(kajson.dumps(vector))
assert vector == restored
```

### Working with Mixed Types

**Full example:** [`ex_12_readme_mixed_types.py`](examples/ex_12_readme_mixed_types.py)

```python
from datetime import datetime, timedelta
from typing import Any, Dict
from pydantic import BaseModel

class Task(BaseModel):
    name: str
    created_at: datetime
    duration: timedelta
    metadata: Dict[str, Any]

# Create mixed-type list
tasks = [
    Task(
        name="Data processing",
        created_at=datetime.now(),
        duration=timedelta(hours=2, minutes=30),
        metadata={"priority": "high", "cpu_cores": 8}
    ),
    {"raw_data": "Some plain dict"},
    datetime.now(),
    ["plain", "list", "items"],
]

# Kajson handles everything!
json_str = kajson.dumps(tasks)
restored_tasks = kajson.loads(json_str)

# Type checking shows proper reconstruction
assert isinstance(restored_tasks[0], Task)
assert isinstance(restored_tasks[0].duration, timedelta)
assert isinstance(restored_tasks[2], datetime)
```

## 🛡️ Error Handling

**Full example:** [`ex_13_readme_error_handling.py`](examples/ex_13_readme_error_handling.py)

Kajson provides clear error messages for validation issues:

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str
    price: float = Field(gt=0)  # Price must be positive

# Invalid data
json_str = '{"name": "Widget", "price": -10, "__class__": "Product", "__module__": "__main__"}'

try:
    product = kajson.loads(json_str)
except kajson.KajsonDecoderError as e:
    print(f"Validation failed: {e}")
    # Output: Validation failed: Could not instantiate pydantic BaseModel...
```

### Dynamic Class Registry

**Full example:** [`ex_14_dynamic_class_registry.py`](examples/ex_14_dynamic_class_registry.py)

Kajson includes a powerful class registry for handling dynamically created classes that aren't available in standard module paths:

```python
from kajson import kajson, kajson_manager
from kajson.kajson_manager import KajsonManager

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
```

**The Class Registry is essential for:**
- 🌐 **Distributed systems** - Classes defined across different services
- ⚙️ **Workflow orchestrators** - Dynamic task definitions at runtime  
- 🔌 **Plugin systems** - Runtime-loaded classes from plugins
- 🚀 **Microservices** - Exchanging complex object definitions
- 🏭 **Dynamic generation** - Any runtime class creation scenarios

### Pydantic Subclass Polymorphism

**Full example:** [`ex_15_pydantic_subclass_polymorphism.py`](examples/ex_15_pydantic_subclass_polymorphism.py)

Kajson perfectly handles polymorphism with Pydantic models, preserving exact subclass types during serialization:

```python
from pydantic import BaseModel

class Animal(BaseModel):
    name: str
    species: str

class Dog(Animal):
    breed: str
    is_good_boy: bool = True

class Pet(BaseModel):
    owner: str
    animal: Animal  # ← Field declared as base class

# Create pet with subclass instance
pet = Pet(
    owner="Alice",
    animal=Dog(name="Buddy", species="Canis lupus", breed="Golden Retriever")  # ← Actual subclass
)

# Serialize and deserialize
json_str = kajson.dumps(pet)
restored_pet = kajson.loads(json_str)

# Subclass type and attributes are perfectly preserved!
assert isinstance(restored_pet.animal, Dog)  # ✅ Still a Dog, not just Animal
assert restored_pet.animal.breed == "Golden Retriever"  # ✅ Subclass attributes preserved
assert restored_pet.animal.is_good_boy is True  # ✅ All fields intact
```

**Perfect for:**
- 🎭 **Polymorphic APIs** - Base class endpoints that handle multiple subclasses
- 🗂️ **Mixed collections** - Lists of base class containing various subclasses  
- 🏗️ **Plugin architectures** - Runtime-loaded implementations of base interfaces
- 📊 **Data modeling** - Complex hierarchies with specialized behaviors


## 🔗 Examples

For detailed examples and tutorials, visit: **[https://pipelex.github.io/kajson/pages/examples/](https://pipelex.github.io/kajson/pages/examples/)**

All code examples from this README are available as executable files in the [`examples/`](examples/) directory:

- [`ex_01_basic_pydantic_serialization.py`](examples/ex_01_basic_pydantic_serialization.py) - Basic Pydantic model serialization
- [`ex_02_nested_models_mixed_types.py`](examples/ex_02_nested_models_mixed_types.py) - Complex nested models with datetime and timedelta
- [`ex_03_custom_classes_json_hooks.py`](examples/ex_03_custom_classes_json_hooks.py) - Point class using `__json_encode__`/`__json_decode__` hooks
- [`ex_04_registering_custom_encoders.py`](examples/ex_04_registering_custom_encoders.py) - Custom type registration
- [`ex_05_mixed_types_lists.py`](examples/ex_05_mixed_types_lists.py) - Lists containing different types (Task, datetime, dict, list, time)
- [`ex_06_error_handling_validation.py`](examples/ex_06_error_handling_validation.py) - Error handling and validation
- [`ex_07_drop_in_replacement.py`](examples/ex_07_drop_in_replacement.py) - Drop-in replacement for standard JSON
- [`ex_08_readme_basic_usage.py`](examples/ex_08_readme_basic_usage.py) - Why Kajson? (README example)
- [`ex_09_readme_complex_nested.py`](examples/ex_09_readme_complex_nested.py) - Complex nested models (README example)
- [`ex_10_readme_custom_registration.py`](examples/ex_10_readme_custom_registration.py) - Custom type registration (README example)
- [`ex_11_readme_custom_hooks.py`](examples/ex_11_readme_custom_hooks.py) - Custom hooks (README example)
- [`ex_12_readme_mixed_types.py`](examples/ex_12_readme_mixed_types.py) - Mixed types (README example)
- [`ex_13_readme_error_handling.py`](examples/ex_13_readme_error_handling.py) - Error handling (README example)
- [`ex_14_dynamic_class_registry.py`](examples/ex_14_dynamic_class_registry.py) - Dynamic class registry for distributed systems and runtime class generation
- [`ex_15_pydantic_subclass_polymorphism.py`](examples/ex_15_pydantic_subclass_polymorphism.py) - Pydantic subclass polymorphism with perfect type preservation

Run any example with:
```bash
cd examples
python ex_01_basic_pydantic_serialization.py
```

## Credits

This project is heavily based on the excellent work from [unijson](https://github.com/bpietropaoli/unijson) by Bastien Pietropaoli and distributed under the same license, [Apache 2.0](LICENSE).

## License

© 2025 Evotis S.A.S. - Licensed under [Apache 2.0](LICENSE)
