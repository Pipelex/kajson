# Basic Usage

This guide covers the fundamental features of Kajson and how to use it as a drop-in replacement for Python's standard `json` module.

## Importing Kajson

You can import Kajson in two ways:

```python
# Option 1: Direct import
import kajson

# Option 2: Drop-in replacement
import kajson as json
```

## Basic Serialization and Deserialization

### Simple Data Types

Kajson handles all standard JSON data types just like the standard `json` module:

```python
import kajson

# Basic types
data = {
    "string": "Hello, World!",
    "number": 42,
    "float": 3.14159,
    "boolean": True,
    "null": None,
    "list": [1, 2, 3],
    "dict": {"nested": "value"}
}

# Serialize to JSON string
json_str = kajson.dumps(data)

# Deserialize back to Python object
restored = kajson.loads(json_str)

assert data == restored  # Perfect reconstruction
```

### Formatting Options

Kajson supports all the standard formatting options:

```python
import kajson

data = {"name": "Alice", "age": 30, "skills": ["Python", "JavaScript"]}

# Pretty printing with indentation
print(kajson.dumps(data, indent=2))

# Compact output without spaces
print(kajson.dumps(data, separators=(',', ':')))

# Sort keys alphabetically
print(kajson.dumps(data, sort_keys=True))

# Combine options
print(kajson.dumps(data, indent=4, sort_keys=True))
```

## Working with Files

### Writing JSON to Files

```python
import kajson

data = {
    "users": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ],
    "total": 2
}

# Write to file
with open("data.json", "w") as f:
    kajson.dump(data, f, indent=2)

# Alternative: dumps then write
json_str = kajson.dumps(data, indent=2)
with open("data2.json", "w") as f:
    f.write(json_str)
```

### Reading JSON from Files

```python
import kajson

# Read from file
with open("data.json", "r") as f:
    data = kajson.load(f)

# Alternative: read then loads
with open("data.json", "r") as f:
    json_str = f.read()
    data = kajson.loads(json_str)
```

## Enhanced Type Support

Unlike standard `json`, Kajson automatically handles many Python types:

### DateTime Objects

```python
import kajson
from datetime import datetime, date, time, timedelta

data = {
    "created_at": datetime.now(),
    "date_only": date.today(),
    "time_only": time(14, 30, 45),
    "duration": timedelta(days=7, hours=3)
}

# Serialize and deserialize
json_str = kajson.dumps(data)
restored = kajson.loads(json_str)

# Types are preserved!
assert isinstance(restored["created_at"], datetime)
assert isinstance(restored["duration"], timedelta)
```

### Lists and Dictionaries with Complex Types

```python
import kajson
from datetime import datetime

# Complex nested structures
data = {
    "timestamps": [datetime.now(), datetime(2025, 1, 1)],
    "events": {
        "start": datetime(2025, 1, 1, 9, 0),
        "end": datetime(2025, 1, 1, 17, 0)
    }
}

# Works seamlessly
json_str = kajson.dumps(data)
restored = kajson.loads(json_str)

# All nested types preserved
for ts in restored["timestamps"]:
    assert isinstance(ts, datetime)
```

## Advanced Options

### Custom Separators

```python
import kajson

data = {"a": 1, "b": 2}

# Default separators
default = kajson.dumps(data)
print(default)  # {"a": 1, "b": 2}

# Custom separators for compact output
compact = kajson.dumps(data, separators=(',', ':'))
print(compact)  # {"a":1,"b":2}

# Custom separators with spaces
spaced = kajson.dumps(data, separators=(', ', ': '))
print(spaced)  # {"a": 1, "b": 2}
```

### Ensure ASCII

```python
import kajson

data = {"greeting": "Hello 世界 🌍"}

# Default: UTF-8 characters preserved
utf8 = kajson.dumps(data)
print(utf8)  # {"greeting": "Hello 世界 🌍"}

# Ensure ASCII: escape non-ASCII characters
ascii_only = kajson.dumps(data, ensure_ascii=True)
print(ascii_only)  # {"greeting": "Hello \\u4e16\\u754c \\ud83c\\udf0d"}
```

## Streaming Large Data

For large datasets, you can use generators and iterative parsing:

```python
import kajson

# Serialize large data in chunks
def generate_large_data():
    for i in range(1000000):
        yield {"id": i, "value": i * 2}

# Write to file efficiently
with open("large_data.json", "w") as f:
    f.write("[")
    for i, item in enumerate(generate_large_data()):
        if i > 0:
            f.write(",")
        f.write(kajson.dumps(item))
    f.write("]")
```

## Common Patterns

### Configuration Files

```python
import kajson
from pathlib import Path

class Config:
    def __init__(self, config_path="config.json"):
        self.path = Path(config_path)
        self.data = self.load()
    
    def load(self):
        if self.path.exists():
            with open(self.path, "r") as f:
                return kajson.load(f)
        return {}
    
    def save(self):
        with open(self.path, "w") as f:
            kajson.dump(self.data, f, indent=2)
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def set(self, key, value):
        self.data[key] = value
        self.save()

# Usage
config = Config()
config.set("api_key", "secret123")
config.set("timeout", 30)
```

### API Responses

```python
import kajson

def create_api_response(data, status="success", message=None):
    response = {
        "status": status,
        "timestamp": kajson.dumps(datetime.now()),  # Will be properly serialized
        "data": data
    }
    if message:
        response["message"] = message
    
    return kajson.dumps(response, indent=2)

# Usage
user_data = {"id": 123, "name": "Alice"}
response = create_api_response(user_data)
print(response)
```

## Best Practices

1. **Always use context managers** when working with files:
   ```python
   with open("file.json", "r") as f:
       data = kajson.load(f)
   ```

2. **Handle exceptions** when loading untrusted data:
   ```python
   try:
       data = kajson.loads(user_input)
   except kajson.JSONDecodeError as e:
       print(f"Invalid JSON: {e}")
   ```

3. **Use appropriate formatting** for your use case:
   - Human-readable: `indent=2` or `indent=4`
   - Network transmission: `separators=(',', ':')` for compact output
   - Configuration files: `indent=2, sort_keys=True` for consistency

## Next Steps

- Learn about [Pydantic Integration](pydantic.md) for working with data models
- Explore [Custom Types](custom-types.md) to extend Kajson's capabilities
- See [Error Handling](error-handling.md) for robust error management 