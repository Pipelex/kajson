# Examples

This section contains practical examples demonstrating how to use Kajson.

## Basic Pydantic Model Serialization

```python
import kajson
from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    created_at: datetime

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
```

## Nested Models with Mixed Types

```python
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta

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
```

## Custom Classes with JSON Hooks

```python
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __json_encode__(self):
        """Called during serialization"""
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def __json_decode__(cls, data: dict):
        """Called during deserialization"""
        return cls(data["x"], data["y"])
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

# Use it directly
point = Point(3.14, 2.71)
json_str = kajson.dumps(point)
restored = kajson.loads(json_str)
assert point == restored
```

## Registering Custom Type Encoders

```python
import kajson
from decimal import Decimal
from pathlib import Path

# Register Decimal support
kajson.UniversalJSONEncoder.register(
    Decimal,
    lambda d: {"decimal": str(d)}
)
kajson.UniversalJSONDecoder.register(
    Decimal,
    lambda data: Decimal(data["decimal"])
)

# Register Path support
kajson.UniversalJSONEncoder.register(
    Path,
    lambda p: {"path": str(p)}
)
kajson.UniversalJSONDecoder.register(
    Path,
    lambda data: Path(data["path"])
)

# Now they work!
data = {
    "price": Decimal("19.99"),
    "config_path": Path("/etc/app/config.json")
}
restored = kajson.loads(kajson.dumps(data))
assert restored["price"] == Decimal("19.99")
assert isinstance(restored["config_path"], Path)
```

## Working with Lists of Mixed Types

```python
from datetime import datetime, date, time
from pydantic import BaseModel

class Task(BaseModel):
    name: str
    due_date: date

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
```

## Error Handling with Validation

```python
from pydantic import BaseModel, Field
import kajson

class Product(BaseModel):
    name: str
    price: float = Field(gt=0)  # Must be positive

# Valid data works fine
product = Product(name="Widget", price=19.99)
json_str = kajson.dumps(product)

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
except kajson.KajsonDecoderError as e:
    print(f"Validation failed: {e}")
    # Output: Validation failed: Could not instantiate pydantic BaseModel...
```

## Drop-in Replacement Usage

```python
# Simply change your import
import kajson as json  # Instead of: import json

# All your existing code works!
data = {"user": "Alice", "logged_in": datetime.now()}
json_str = json.dumps(data)  # Works with datetime!
restored = json.loads(json_str)

# Or use kajson directly
import kajson
json_str = kajson.dumps(data)
```
