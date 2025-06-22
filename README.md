# 🚀 Kajson - Universal JSON Encoder/Decoder for Python

[![PyPI version](https://img.shields.io/pypi/v/kajson.svg)](https://pypi.org/project/kajson/)
[![Python versions](https://img.shields.io/pypi/pyversions/kajson.svg)](https://pypi.org/project/kajson/)
[![License](https://img.shields.io/pypi/l/kajson.svg)](https://github.com/PipelexLab/kajson/blob/main/LICENSE)

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

```python
import kajson
from datetime import datetime, date
from pydantic import BaseModel

# Pydantic models with datetime fields
class Article(BaseModel):
    title: str
    published_at: datetime
    tags: list[str]

article = Article(
    title="Why Kajson is awesome",
    published_at=datetime.now(),
    tags=["python", "json", "pydantic"]
)

# Serialize to JSON
json_str = kajson.dumps(article, indent=2)

# Deserialize back to object
restored = kajson.loads(json_str)
assert article == restored  # ✅ Perfect reconstruction!
```

### Working with Complex Nested Models

```python
from typing import List
from pydantic import BaseModel
from datetime import datetime

class Comment(BaseModel):
    author: str
    content: str
    created_at: datetime

class BlogPost(BaseModel):
    title: str
    content: str
    published_at: datetime
    comments: List[Comment]
    metadata: dict

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

## 🔧 Advanced Features

### Custom Type Registration

Register encoders/decoders for any type:

```python
from decimal import Decimal
from pathlib import Path
import kajson

# Register Decimal support
def encode_decimal(value: Decimal) -> dict:
    return {"decimal": str(value)}

def decode_decimal(data: dict) -> Decimal:
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

Add JSON support to your own classes:

```python
class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __json_encode__(self):
        """Called by Kajson during serialization"""
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def __json_decode__(cls, data: dict):
        """Called by Kajson during deserialization"""
        return cls(data["x"], data["y"])
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

# Works automatically!
vector = Vector(3.14, 2.71)
restored = kajson.loads(kajson.dumps(vector))
assert vector == restored
```

### Working with Mixed Types

```python
from datetime import datetime, timedelta
from pydantic import BaseModel

class Task(BaseModel):
    name: str
    created_at: datetime
    duration: timedelta
    metadata: dict

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

## 📚 Use Cases

- **REST APIs**: Serialize Pydantic models for API responses
- **Data Persistence**: Save complex objects to JSON files
- **Message Queues**: Send rich objects through Redis/RabbitMQ
- **Configuration**: Store config with proper types
- **Data Science**: Serialize numpy arrays, pandas DataFrames (with custom encoders)

## Credits

This project is heavily based on the excellent work from [unijson](https://github.com/bpietropaoli/unijson) by Bastien Pietropaoli and distributed under the same license, [Apache 2.0](LICENSE).

## License

© 2025 Evotis S.A.S. - Licensed under [Apache 2.0](LICENSE)
