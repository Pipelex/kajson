# KajsonManager API Reference

The `KajsonManager` class provides a singleton interface for managing kajson operations, including class registry management and logger configuration.

## KajsonManager Class

### Constructor

```python
def __init__(
    self,
    logger_channel_name: Optional[str] = None,
    class_registry: Optional[ClassRegistryAbstract] = None,
) -> None
```

Initialize the KajsonManager singleton instance.

**Parameters:**

- `logger_channel_name`: Name of the logger channel (default: "kajson")
- `class_registry`: Custom class registry implementation (default: ClassRegistry())

!!! note
    KajsonManager is a singleton class. Multiple calls to the constructor will return the same instance.

### Class Methods

#### get_instance

```python
@classmethod
def get_instance(cls) -> KajsonManager
```

Get the singleton instance of KajsonManager. Creates one if it doesn't exist.

**Returns:** The singleton KajsonManager instance

**Example:**

```python
from kajson.kajson_manager import KajsonManager

manager = KajsonManager.get_instance()
```

#### teardown

```python
@classmethod
def teardown(cls) -> None
```

Destroy the singleton instance. Useful for testing or cleanup scenarios.

**Example:**

```python
from kajson.kajson_manager import KajsonManager

# Clean up the singleton instance
KajsonManager.teardown()
```

#### get_class_registry

```python
@classmethod
def get_class_registry(cls) -> ClassRegistryAbstract
```

Get the class registry from the singleton instance.

**Returns:** The class registry instance used for managing custom type serialization

**Example:**

```python
from kajson.kajson_manager import KajsonManager

registry = KajsonManager.get_class_registry()
```

## Usage Examples

### Basic Usage

```python
from kajson.kajson_manager import KajsonManager

# Get the singleton instance
manager = KajsonManager.get_instance()

# Access the class registry
registry = manager._class_registry
# or use the class method
registry = KajsonManager.get_class_registry()
```

### Custom Configuration

```python
from kajson.kajson_manager import KajsonManager
from kajson.class_registry import ClassRegistry

# Initialize with custom logger channel
manager = KajsonManager(logger_channel_name="my_logger")

# Or with custom class registry
custom_registry = ClassRegistry()
manager = KajsonManager(class_registry=custom_registry)
```

### Testing and Cleanup

```python
from kajson.kajson_manager import KajsonManager

# In test setup - ensure clean state
KajsonManager.teardown()

# Use the manager in tests
manager = KajsonManager.get_instance()

# In test teardown
KajsonManager.teardown()
```

!!! tip
    The KajsonManager is primarily used internally by kajson. Most users won't need to interact with it directly unless they're implementing custom serialization logic or need to access the class registry programmatically. 