# User Guide Overview

Welcome to the Kajson User Guide! This comprehensive guide will help you master all aspects of Kajson, from basic usage to advanced features.

## What You'll Learn

This guide is organized into several sections, each focusing on different aspects of Kajson:

### [Basic Usage](basic-usage.md)
Learn the fundamentals of using Kajson as a drop-in replacement for Python's standard json module. Covers:

- Basic serialization and deserialization
- Working with files
- Formatting options
- Common patterns

### [Pydantic Integration](pydantic.md)
Discover how Kajson seamlessly integrates with Pydantic v2 models:

- Automatic model serialization
- Validation during deserialization
- Nested model support
- Advanced Pydantic features

### [Custom Types](custom-types.md)
Learn how to extend Kajson to support your own custom types:

- Registering custom encoders/decoders
- Using the `__json_encode__` and `__json_decode__` hooks
- Best practices for custom type support
- Common patterns and examples

### [Error Handling](error-handling.md)
Understand how to handle errors and edge cases:

- Common error scenarios
- Validation errors with Pydantic
- Debugging serialization issues
- Best practices for robust code

## Key Concepts

### Type Preservation

Kajson's main innovation is automatic type preservation. When you serialize an object, Kajson adds metadata that allows perfect reconstruction:

```python
from datetime import datetime
import kajson

# Original object
data = {"created": datetime.now(), "count": 42}

# Serialize
json_str = kajson.dumps(data)

# Deserialize - types are preserved!
restored = kajson.loads(json_str)
assert isinstance(restored["created"], datetime)
```

### Drop-in Replacement

Kajson is designed to be a drop-in replacement for the standard `json` module:

```python
# Change this:
import json

# To this:
import kajson as json

# All your existing code continues to work!
```

### Extensibility

Kajson is built to be extensible. You can easily add support for any type:

```python
import kajson
from decimal import Decimal

# Register Decimal support
kajson.UniversalJSONEncoder.register(
    Decimal,
    lambda d: {"value": str(d)}
)
kajson.UniversalJSONDecoder.register(
    Decimal,
    lambda data: Decimal(data["value"])
)
```

## Best Practices

1. **Use Type Hints**: Always use type hints in your Pydantic models for better IDE support and documentation
2. **Handle Errors**: Always wrap deserialization in try-except blocks when dealing with untrusted data
3. **Test Serialization**: Test that your objects can round-trip (serialize and deserialize) correctly
4. **Keep It Simple**: Start with built-in support before creating custom encoders

## Getting Help

- Check the [API Reference](../api/kajson.md) for detailed function documentation
- Browse [Examples](../examples/index.md) for real-world use cases
- Visit our [GitHub repository](https://github.com/Pipelex/kajson) for issues and discussions

## Next Steps

Ready to dive in? Start with [Basic Usage](basic-usage.md) to learn the fundamentals! 