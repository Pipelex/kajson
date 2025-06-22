# Quick Start Guide

Get up and running with Kajson in minutes! This guide covers the most common use cases.

## Basic Usage

Kajson is designed as a drop-in replacement for Python's standard `json` module:

```python
import kajson

# Works just like standard json
data = {"name": "Alice", "age": 30}
json_str = kajson.dumps(data)
restored = kajson.loads(json_str)
```

## Working with Pydantic Models

The real power of Kajson comes when working with complex objects:

```python
from datetime import datetime
from pydantic import BaseModel
import kajson

class User(BaseModel):
    name: str
    email: str
    created_at: datetime
    is_active: bool = True

# Create a user
user = User(
    name="Alice",
    email="alice@example.com",
    created_at=datetime.now()
)

# Serialize to JSON
json_str = kajson.dumps(user, indent=2)
print(json_str)

# Deserialize back to User object
restored_user = kajson.loads(json_str)
assert isinstance(restored_user, User)
assert user == restored_user
```

## DateTime Support

Kajson automatically handles datetime objects:

```python
from datetime import datetime, date, time, timedelta
import kajson

data = {
    "meeting_date": date(2025, 1, 15),
    "meeting_time": time(14, 30),
    "meeting_datetime": datetime(2025, 1, 15, 14, 30),
    "duration": timedelta(hours=1, minutes=30)
}

# Serialize and deserialize
json_str = kajson.dumps(data)
restored = kajson.loads(json_str)

# All types are preserved
assert isinstance(restored["meeting_date"], date)
assert isinstance(restored["duration"], timedelta)
```

## Nested Objects

Kajson handles complex nested structures seamlessly:

```python
from typing import List
from pydantic import BaseModel
from datetime import datetime

class Comment(BaseModel):
    text: str
    author: str
    created_at: datetime

class Post(BaseModel):
    title: str
    content: str
    comments: List[Comment]
    tags: List[str]

# Create nested structure
post = Post(
    title="Getting Started with Kajson",
    content="Kajson makes JSON serialization easy...",
    comments=[
        Comment(text="Great post!", author="Bob", created_at=datetime.now()),
        Comment(text="Very helpful", author="Carol", created_at=datetime.now())
    ],
    tags=["python", "json", "tutorial"]
)

# Works perfectly
json_str = kajson.dumps(post)
restored_post = kajson.loads(json_str)
```

## File Operations

Just like standard json, Kajson supports file operations:

```python
import kajson

# Save to file
with open("data.json", "w") as f:
    kajson.dump(user, f, indent=2)

# Load from file
with open("data.json", "r") as f:
    loaded_user = kajson.load(f)
```

## Next Steps

- Learn about [Basic Usage](guide/basic-usage.md) patterns
- Explore [Pydantic Integration](guide/pydantic.md) in depth
- Discover how to work with [Custom Types](guide/custom-types.md)
- Check out practical [Examples](examples/index.md) 