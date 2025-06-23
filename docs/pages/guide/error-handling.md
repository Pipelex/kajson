# Error Handling

Learn how to handle errors gracefully when working with Kajson, including validation errors, serialization failures, and debugging techniques.

## Common Error Types

### JSONDecodeError

The standard JSON decode error when parsing invalid JSON:

```python
import kajson

# Invalid JSON syntax
try:
    kajson.loads('{"name": "Alice",}')  # Trailing comma
except kajson.JSONDecodeError as e:
    print(f"JSON syntax error: {e}")
    print(f"Position: {e.pos}")

# Incomplete JSON
try:
    kajson.loads('{"name": "Alice"')  # Missing closing brace
except kajson.JSONDecodeError as e:
    print(f"Incomplete JSON: {e}")
```

### KajsonDecoderError

Kajson-specific errors during type reconstruction:

```python
import kajson
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0, le=150)

# Validation error
try:
    invalid_json = '{"name": "", "age": 200, "__class__": "User", "__module__": "__main__"}'
    user = kajson.loads(invalid_json)
except kajson.KajsonDecoderError as e:
    print(f"Validation failed: {e}")
    # Access the underlying Pydantic validation error if needed
    if hasattr(e, '__cause__'):
        print(f"Details: {e.__cause__}")
```

### Type Registration Errors

Errors when working with custom type registration:

```python
import kajson

# Attempting to decode unregistered type
try:
    json_str = '{"__class__": "UnknownType", "__module__": "unknown", "data": 123}'
    result = kajson.loads(json_str)
except kajson.KajsonDecoderError as e:
    print(f"Unknown type: {e}")

# Bad encoder/decoder functions
from decimal import Decimal

try:
    # This encoder returns wrong type (should return dict)
    kajson.UniversalJSONEncoder.register(
        Decimal,
        lambda d: str(d)  # Wrong! Should return dict
    )
except Exception as e:
    print(f"Registration error: {e}")
```

## Handling Pydantic Validation Errors

### Basic Validation Handling

```python
import kajson
from pydantic import BaseModel, Field, ValidationError

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)

def safe_load_product(json_str: str) -> Product | None:
    try:
        return kajson.loads(json_str)
    except kajson.KajsonDecoderError as e:
        # Check if it's a Pydantic validation error
        if isinstance(e.__cause__, ValidationError):
            print("Validation errors:")
            for error in e.__cause__.errors():
                print(f"  - {error['loc']}: {error['msg']}")
        else:
            print(f"Decoder error: {e}")
        return None
    except kajson.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return None

# Test with various inputs
test_cases = [
    '{"name": "Laptop", "price": 999.99, "stock": 10, "__class__": "Product", "__module__": "__main__"}',
    '{"name": "", "price": 999.99, "stock": 10, "__class__": "Product", "__module__": "__main__"}',
    '{"name": "Laptop", "price": -100, "stock": 10, "__class__": "Product", "__module__": "__main__"}',
    'invalid json'
]

for json_str in test_cases:
    print(f"\nTesting: {json_str[:50]}...")
    product = safe_load_product(json_str)
    if product:
        print(f"Success: {product.name}")
```

### Collecting All Validation Errors

```python
import kajson
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any

class Address(BaseModel):
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    zip_code: str = Field(pattern=r'^\d{5}$')

def get_validation_errors(json_str: str) -> Dict[str, List[str]]:
    """Extract all validation errors from a JSON string"""
    errors = {}
    
    try:
        kajson.loads(json_str)
    except kajson.KajsonDecoderError as e:
        if isinstance(e.__cause__, ValidationError):
            for error in e.__cause__.errors():
                field = '.'.join(str(x) for x in error['loc'])
                if field not in errors:
                    errors[field] = []
                errors[field].append(error['msg'])
    
    return errors

# Test with invalid data
invalid_address = '''{
    "street": "",
    "city": "",
    "zip_code": "ABC123",
    "__class__": "Address",
    "__module__": "__main__"
}'''

errors = get_validation_errors(invalid_address)
for field, messages in errors.items():
    print(f"{field}: {', '.join(messages)}")
```

## Debugging Serialization Issues

### Debugging Complex Objects

```python
import kajson
from typing import Any
import json

def debug_serialize(obj: Any, indent: int = 2) -> str:
    """Serialize with detailed error information"""
    try:
        return kajson.dumps(obj, indent=indent)
    except Exception as e:
        print(f"Serialization failed for type {type(obj)}: {e}")
        
        # Try to identify the problematic part
        if hasattr(obj, '__dict__'):
            print("Object attributes:")
            for key, value in obj.__dict__.items():
                try:
                    kajson.dumps(value)
                    print(f"  ✓ {key}: {type(value).__name__}")
                except Exception as attr_e:
                    print(f"  ✗ {key}: {type(value).__name__} - {attr_e}")
        
        raise

# Example with problematic object
class ComplexObject:
    def __init__(self):
        self.name = "Test"
        self.data = [1, 2, 3]
        self.file = open(__file__, 'r')  # This will cause an error

try:
    obj = ComplexObject()
    json_str = debug_serialize(obj)
except Exception as e:
    print(f"Final error: {e}")
finally:
    obj.file.close()
```

### Custom Error Messages

```python
import kajson
from typing import Any

class SerializationError(Exception):
    """Custom error for serialization issues"""
    def __init__(self, obj: Any, original_error: Exception):
        self.obj = obj
        self.original_error = original_error
        super().__init__(
            f"Failed to serialize {type(obj).__name__}: {original_error}"
        )

def safe_dumps(obj: Any, **kwargs) -> str:
    """Serialize with custom error handling"""
    try:
        return kajson.dumps(obj, **kwargs)
    except Exception as e:
        raise SerializationError(obj, e)

# Usage
try:
    result = safe_dumps({"data": lambda x: x})  # Lambda can't be serialized
except SerializationError as e:
    print(f"Custom error: {e}")
    print(f"Object type: {type(e.obj)}")
    print(f"Original error: {e.original_error}")
```

## Error Recovery Strategies

### Fallback Values

```python
import kajson
from typing import TypeVar, Type, Optional, Callable

T = TypeVar('T')

def loads_with_fallback(
    json_str: str,
    expected_type: Type[T],
    fallback_factory: Callable[[], T]
) -> T:
    """Load JSON with fallback on error"""
    try:
        result = kajson.loads(json_str)
        if not isinstance(result, expected_type):
            print(f"Warning: Expected {expected_type}, got {type(result)}")
            return fallback_factory()
        return result
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return fallback_factory()

# Usage
from pydantic import BaseModel

class Config(BaseModel):
    timeout: int = 30
    retries: int = 3
    debug: bool = False

def default_config() -> Config:
    return Config()

# Various test cases
test_cases = [
    '{"timeout": 60, "retries": 5, "debug": true, "__class__": "Config", "__module__": "__main__"}',
    'invalid json',
    '{"wrong": "data"}',
]

for json_str in test_cases:
    config = loads_with_fallback(json_str, Config, default_config)
    print(f"Config: timeout={config.timeout}, retries={config.retries}")
```

### Partial Recovery

```python
import kajson
from typing import Dict, Any, List

def recover_partial_data(json_str: str) -> Dict[str, Any]:
    """Try to recover as much data as possible"""
    try:
        return kajson.loads(json_str)
    except kajson.JSONDecodeError:
        # Try to fix common issues
        fixed = json_str
        
        # Remove trailing commas
        import re
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        
        # Try again
        try:
            return kajson.loads(fixed)
        except:
            # Last resort: try to extract key-value pairs
            result = {}
            pattern = r'"(\w+)"\s*:\s*("(?:[^"\\]|\\.)*"|\d+|true|false|null)'
            matches = re.findall(pattern, json_str)
            for key, value in matches:
                try:
                    result[key] = kajson.loads(value)
                except:
                    result[key] = value
            return result

# Test with malformed JSON
malformed = '{"name": "Alice", "age": 30, "active": true,}'
recovered = recover_partial_data(malformed)
print(f"Recovered: {recovered}")
```

## Logging and Monitoring

### Structured Error Logging

```python
import kajson
import logging
from typing import Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JsonProcessor:
    def __init__(self):
        self.error_count = 0
        self.success_count = 0
    
    def process(self, json_str: str, source: str = "unknown") -> Optional[Any]:
        """Process JSON with detailed logging"""
        start_time = datetime.now()
        
        try:
            result = kajson.loads(json_str)
            self.success_count += 1
            
            logger.info(
                "JSON processed successfully",
                extra={
                    "source": source,
                    "size": len(json_str),
                    "type": type(result).__name__,
                    "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
            )
            
            return result
            
        except kajson.JSONDecodeError as e:
            self.error_count += 1
            logger.error(
                "JSON syntax error",
                extra={
                    "source": source,
                    "error": str(e),
                    "position": e.pos if hasattr(e, 'pos') else None,
                    "preview": json_str[:100] + "..." if len(json_str) > 100 else json_str
                }
            )
            
        except kajson.KajsonDecoderError as e:
            self.error_count += 1
            logger.error(
                "Type reconstruction error",
                extra={
                    "source": source,
                    "error": str(e),
                    "cause": str(e.__cause__) if hasattr(e, '__cause__') else None
                }
            )
            
        except Exception as e:
            self.error_count += 1
            logger.exception(
                "Unexpected error",
                extra={
                    "source": source,
                    "error_type": type(e).__name__
                }
            )
        
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics"""
        total = self.success_count + self.error_count
        return {
            "total": total,
            "success": self.success_count,
            "errors": self.error_count,
            "success_rate": self.success_count / total if total > 0 else 0
        }

# Usage
processor = JsonProcessor()

test_data = [
    ('{"valid": true}', "api_response"),
    ('invalid json', "user_input"),
    ('{"name": "test"}', "database"),
]

for json_str, source in test_data:
    processor.process(json_str, source)

print(f"Stats: {processor.get_stats()}")
```

## Best Practices

### 1. Always Handle Exceptions

```python
import kajson

def load_data(json_str: str) -> Any:
    """Always wrap loads in try-except"""
    try:
        return kajson.loads(json_str)
    except (kajson.JSONDecodeError, kajson.KajsonDecoderError) as e:
        # Handle specific errors
        logger.error(f"Failed to load JSON: {e}")
        raise
    except Exception as e:
        # Catch unexpected errors
        logger.exception("Unexpected error in JSON loading")
        raise
```

### 2. Provide Context in Errors

```python
class DataLoadError(Exception):
    """Custom error with context"""
    def __init__(self, filename: str, line_num: int, original_error: Exception):
        super().__init__(
            f"Failed to load data from {filename}, line {line_num}: {original_error}"
        )
        self.filename = filename
        self.line_num = line_num
        self.original_error = original_error
```

### 3. Validate Before Serializing

```python
def safe_serialize(obj: Any) -> Optional[str]:
    """Validate object before serialization"""
    # Check for known problematic types
    if hasattr(obj, '__call__'):
        logger.warning(f"Cannot serialize callable: {obj}")
        return None
    
    try:
        return kajson.dumps(obj)
    except Exception as e:
        logger.error(f"Serialization failed: {e}")
        return None
```

## Next Steps

- Review practical [Examples](../examples/index.md) for real-world error handling
- Check the [API Reference](../api/kajson.md) for detailed error specifications
- Learn about [Custom Types](custom-types.md) to avoid serialization errors 