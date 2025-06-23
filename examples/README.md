# Kajson Examples

This directory contains runnable Python examples demonstrating all the features of Kajson. Each example is self-contained and can be run independently.

## Examples from Documentation

### Basic Usage Examples
- **01_basic_pydantic_serialization.py** - Basic Pydantic model with datetime serialization
- **08_readme_basic_usage.py** - Shows the problem with standard JSON and how Kajson solves it

### Complex Nested Models
- **02_nested_models_mixed_types.py** - BlogPost with Comment models, timedelta support
- **09_readme_complex_nested.py** - Complex nested structures with metadata

### Custom Type Support
- **03_custom_classes_json_hooks.py** - Point class using `__json_encode__`/`__json_decode__` hooks
- **11_readme_custom_hooks.py** - Vector class with custom JSON hooks
- **04_registering_custom_encoders.py** - Register Decimal and Path type encoders
- **10_readme_custom_registration.py** - Advanced custom type registration

### Mixed Type Handling
- **05_mixed_types_lists.py** - Lists containing different types (Task, datetime, dict, list, time)
- **12_readme_mixed_types.py** - Complex mixed-type data structures with timedelta

### Error Handling
- **06_error_handling_validation.py** - Pydantic validation error handling
- **13_readme_error_handling.py** - Clear error messages for validation failures

### Integration Examples
- **07_drop_in_replacement.py** - Using Kajson as a drop-in replacement for standard json

## Running the Examples

Each example can be run independently:

```bash
# Run a specific example
python examples/01_basic_pydantic_serialization.py

# Or run from the examples directory
cd examples
python 01_basic_pydantic_serialization.py
```

## Example Output

Each example includes:
- ✅ Clear success indicators
- 🔍 Type checking demonstrations
- 📊 Before/after comparisons
- 💡 Explanatory comments

## Requirements

All examples require:
- Python 3.9+
- kajson (installed in development mode)
- pydantic (for BaseModel examples)

The examples use only standard library imports plus kajson and pydantic, making them easy to run and understand. 