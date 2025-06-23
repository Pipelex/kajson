# Custom Types

Learn how to extend Kajson to support any custom type through registration or built-in hooks.

## Registration System

### Basic Registration

The simplest way to add support for a custom type is through the registration system:

```python
import kajson
from decimal import Decimal

# Register encoder
def encode_decimal(value: Decimal) -> dict:
    return {"__decimal__": str(value)}

# Register decoder
def decode_decimal(data: dict) -> Decimal:
    return Decimal(data["__decimal__"])

# Register both
kajson.UniversalJSONEncoder.register(Decimal, encode_decimal)
kajson.UniversalJSONDecoder.register(Decimal, decode_decimal)

# Now Decimal works seamlessly
data = {"price": Decimal("19.99"), "tax": Decimal("1.50")}
json_str = kajson.dumps(data)
restored = kajson.loads(json_str)

assert restored["price"] == Decimal("19.99")
assert isinstance(restored["price"], Decimal)
```

### Registration with Type Checking

For more robust implementations, include type checking:

```python
import kajson
from pathlib import Path

def encode_path(path: Path) -> dict:
    return {
        "__path__": str(path),
        "is_absolute": path.is_absolute()
    }

def decode_path(data: dict) -> Path:
    if "__path__" not in data:
        raise ValueError("Invalid Path data")
    return Path(data["__path__"])

kajson.UniversalJSONEncoder.register(Path, encode_path)
kajson.UniversalJSONDecoder.register(Path, decode_path)

# Usage
config = {
    "project_root": Path("/home/user/project"),
    "config_file": Path("config/settings.json")
}

json_str = kajson.dumps(config)
restored = kajson.loads(json_str)
```

## Custom Class Hooks

### Using __json_encode__ and __json_decode__

Classes can define their own serialization behavior:

```python
import kajson
from typing import Tuple

class Color:
    def __init__(self, r: int, g: int, b: int, name: str = ""):
        self.r = r
        self.g = g
        self.b = b
        self.name = name
    
    def __json_encode__(self) -> dict:
        """Called by Kajson during serialization"""
        return {
            "rgb": (self.r, self.g, self.b),
            "name": self.name,
            "hex": f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        }
    
    @classmethod
    def __json_decode__(cls, data: dict) -> "Color":
        """Called by Kajson during deserialization"""
        r, g, b = data["rgb"]
        return cls(r, g, b, data.get("name", ""))
    
    def __eq__(self, other):
        return (self.r, self.g, self.b, self.name) == (other.r, other.g, other.b, other.name)

# Works automatically
red = Color(255, 0, 0, "red")
json_str = kajson.dumps(red)
restored = kajson.loads(json_str)

assert red == restored
```

### Complex Custom Types

```python
import kajson
from typing import List, Optional
import numpy as np

class Matrix:
    def __init__(self, data: List[List[float]]):
        self.data = np.array(data)
        self.shape = self.data.shape
    
    def __json_encode__(self) -> dict:
        return {
            "data": self.data.tolist(),
            "shape": self.shape,
            "dtype": str(self.data.dtype)
        }
    
    @classmethod
    def __json_decode__(cls, data: dict) -> "Matrix":
        return cls(data["data"])
    
    def __eq__(self, other):
        return np.array_equal(self.data, other.data)

# Usage
matrix = Matrix([[1, 2, 3], [4, 5, 6]])
json_str = kajson.dumps(matrix)
restored = kajson.loads(json_str)

assert matrix == restored
```

## Advanced Registration Patterns

### Registering Multiple Types at Once

```python
import kajson
from fractions import Fraction
from ipaddress import IPv4Address, IPv6Address

# Define encoders/decoders
type_handlers = {
    Fraction: {
        "encode": lambda f: {"num": f.numerator, "den": f.denominator},
        "decode": lambda d: Fraction(d["num"], d["den"])
    },
    IPv4Address: {
        "encode": lambda ip: {"ipv4": str(ip)},
        "decode": lambda d: IPv4Address(d["ipv4"])
    },
    IPv6Address: {
        "encode": lambda ip: {"ipv6": str(ip)},
        "decode": lambda d: IPv6Address(d["ipv6"])
    }
}

# Register all at once
for type_class, handlers in type_handlers.items():
    kajson.UniversalJSONEncoder.register(type_class, handlers["encode"])
    kajson.UniversalJSONDecoder.register(type_class, handlers["decode"])

# All types now work
data = {
    "fraction": Fraction(3, 4),
    "ipv4": IPv4Address("192.168.1.1"),
    "ipv6": IPv6Address("2001:db8::1")
}

json_str = kajson.dumps(data)
restored = kajson.loads(json_str)
```

### Conditional Registration

```python
import kajson
import platform

# Register platform-specific types
if platform.system() == "Windows":
    from pathlib import WindowsPath
    
    kajson.UniversalJSONEncoder.register(
        WindowsPath,
        lambda p: {"windows_path": str(p)}
    )
    kajson.UniversalJSONDecoder.register(
        WindowsPath,
        lambda d: WindowsPath(d["windows_path"])
    )
```

## Working with Third-Party Libraries

### NumPy Arrays

```python
import kajson
import numpy as np

def encode_ndarray(arr: np.ndarray) -> dict:
    return {
        "data": arr.tolist(),
        "dtype": str(arr.dtype),
        "shape": arr.shape
    }

def decode_ndarray(data: dict) -> np.ndarray:
    arr = np.array(data["data"], dtype=data["dtype"])
    return arr.reshape(data["shape"])

kajson.UniversalJSONEncoder.register(np.ndarray, encode_ndarray)
kajson.UniversalJSONDecoder.register(np.ndarray, decode_ndarray)

# Usage
data = {
    "matrix": np.array([[1, 2], [3, 4]]),
    "vector": np.array([1.0, 2.0, 3.0])
}

json_str = kajson.dumps(data)
restored = kajson.loads(json_str)

assert np.array_equal(data["matrix"], restored["matrix"])
```

### Pandas DataFrames

```python
import kajson
import pandas as pd

def encode_dataframe(df: pd.DataFrame) -> dict:
    return {
        "data": df.to_dict(orient="records"),
        "columns": df.columns.tolist(),
        "index": df.index.tolist()
    }

def decode_dataframe(data: dict) -> pd.DataFrame:
    df = pd.DataFrame(data["data"])
    df.index = data["index"]
    return df[data["columns"]]  # Preserve column order

kajson.UniversalJSONEncoder.register(pd.DataFrame, encode_dataframe)
kajson.UniversalJSONDecoder.register(pd.DataFrame, decode_dataframe)

# Usage
df = pd.DataFrame({
    "name": ["Alice", "Bob", "Carol"],
    "age": [25, 30, 35],
    "city": ["NYC", "LA", "Chicago"]
})

json_str = kajson.dumps(df)
restored = kajson.loads(json_str)

assert df.equals(restored)
```

## Best Practices

### 1. Use Unique Keys

Always use unique keys in your encoded data to avoid conflicts:

```python
# Good - unique key unlikely to conflict
def encode_custom(value):
    return {"__mylib_custom__": value.data}

# Bad - generic key might conflict
def encode_custom(value):
    return {"data": value.data}
```

### 2. Include Version Information

For long-term compatibility, include version information:

```python
def encode_complex_type(value):
    return {
        "__mytype__": {
            "version": 1,
            "data": value.serialize()
        }
    }

def decode_complex_type(data):
    version = data["__mytype__"]["version"]
    if version == 1:
        return MyType.deserialize(data["__mytype__"]["data"])
    else:
        raise ValueError(f"Unsupported version: {version}")
```

### 3. Handle Edge Cases

Always handle None and edge cases:

```python
def encode_custom(value):
    if value is None:
        return None
    return {"__custom__": value.to_dict()}

def decode_custom(data):
    if data is None:
        return None
    if "__custom__" not in data:
        raise ValueError("Invalid custom data")
    return CustomType.from_dict(data["__custom__"])
```

### 4. Validate Input in Decoders

```python
def decode_color(data: dict) -> Color:
    # Validate required fields
    if not all(key in data for key in ["r", "g", "b"]):
        raise ValueError("Missing required color components")
    
    # Validate ranges
    r, g, b = data["r"], data["g"], data["b"]
    if not all(0 <= c <= 255 for c in [r, g, b]):
        raise ValueError("Color values must be 0-255")
    
    return Color(r, g, b)
```

## Creating Reusable Type Packages

You can create a package of custom type handlers:

```python
# my_kajson_types.py
import kajson
from typing import Dict, Type, Callable, Tuple

class KajsonTypeRegistry:
    def __init__(self):
        self.types: Dict[Type, Tuple[Callable, Callable]] = {}
    
    def register(self, type_class: Type, encoder: Callable, decoder: Callable):
        self.types[type_class] = (encoder, decoder)
    
    def install(self):
        """Install all registered types into Kajson"""
        for type_class, (encoder, decoder) in self.types.items():
            kajson.UniversalJSONEncoder.register(type_class, encoder)
            kajson.UniversalJSONDecoder.register(type_class, decoder)

# Create registry
registry = KajsonTypeRegistry()

# Add types
from decimal import Decimal
registry.register(
    Decimal,
    lambda d: {"decimal": str(d)},
    lambda data: Decimal(data["decimal"])
)

# Usage in your app
from my_kajson_types import registry
registry.install()
```

## Next Steps

- Explore [Error Handling](error-handling.md) for robust serialization
- Check out practical [Examples](../examples/index.md)
- Review the [API Reference](../api/kajson.md) for detailed documentation 