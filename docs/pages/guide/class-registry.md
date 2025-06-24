# Class Registry

The Class Registry is a powerful feature in kajson that solves a critical problem: deserializing classes that aren't available in the standard module path. This is essential for distributed systems, dynamic class generation, and other advanced scenarios.

## Overview

When kajson deserializes a JSON string containing class metadata (`__class__` and `__module__`), it needs to locate and instantiate the appropriate class. By default, it:

1. Checks if the module is already imported
2. Attempts to import the module dynamically
3. Retrieves the class from the module

However, this approach fails when:

- Classes are created dynamically at runtime
- Classes come from remote systems or distributed services
- Module paths don't exist in the current environment
- Classes are generated from workflow definitions or configurations

The Class Registry provides a solution by maintaining a centralized registry of classes that can be looked up by name during deserialization.

## When to Use the Class Registry

You need the Class Registry when dealing with:

- **🌐 Distributed Systems**: Classes defined in different services or microservices
- **🔄 Dynamic Class Generation**: Classes created at runtime from configurations or definitions
- **🧩 Plugin Systems**: Dynamically loaded plugins with custom classes
- **📊 Workflow Orchestrators**: Task definitions created from workflow specifications
- **🔌 Remote APIs**: Classes received over the network that need to be reconstructed locally
- **⚡ Runtime Type Systems**: Classes that don't exist until runtime

## Basic Usage

### Getting the Registry

The class registry is managed by the `KajsonManager` singleton:

```python
from kajson.kajson_manager import KajsonManager

# Get the global class registry
registry = KajsonManager.get_class_registry()
```

### Registering Classes

#### Register a Single Class

```python
from pydantic import BaseModel

class MyModel(BaseModel):
    name: str
    value: int

# Register with default name (class name)
registry.register_class(MyModel)

# Register with custom name
registry.register_class(MyModel, "CustomModelName")
```

#### Register Multiple Classes

```python
# Register as a list (uses class names)
registry.register_classes([Model1, Model2, Model3])

# Register as a dictionary (custom names)
registry.register_classes_dict({
    "FirstModel": Model1,
    "SecondModel": Model2,
    "ThirdModel": Model3
})
```

### Retrieving Classes

```python
# Get a class (returns None if not found)
model_class = registry.get_class("MyModel")

# Get a required class (raises exception if not found)
model_class = registry.get_required_class("MyModel")

# Get a required subclass (with type checking)
model_class = registry.get_required_subclass("MyModel", BaseModel)

# Get a required BaseModel
model_class = registry.get_required_base_model("MyModel")
```

### Checking Class Existence

```python
# Check if a class exists
if registry.has_class("MyModel"):
    print("MyModel is registered")

# Check if a subclass exists
if registry.has_subclass("MyModel", BaseModel):
    print("MyModel is a registered BaseModel")
```

### Unregistering Classes

```python
# Unregister by class type
registry.unregister_class(MyModel)

# Unregister by name
registry.unregister_class_by_name("MyModel")

# Clear all registrations
registry.teardown()
```

## Complete Example: Dynamic Class from Remote System

Here's a real-world example showing how the class registry enables deserialization of dynamically created classes:

```python
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from kajson import kajson
from kajson.kajson_manager import KajsonManager
from kajson.exceptions import KajsonDecoderError

# Simulate receiving a class definition from a remote system
remote_class_definition = '''
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class RemoteTask(BaseModel):
    """A task definition received from a distributed system."""
    task_id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Task name")
    priority: int = Field(default=1, ge=1, le=10, description="Task priority")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Task payload")
    
    def get_info(self) -> str:
        return f"Task {self.task_id}: {self.name} (priority: {self.priority})"
'''

# Execute the remote class definition
remote_namespace: Dict[str, Any] = {}
exec(remote_class_definition, remote_namespace)
RemoteTask = remote_namespace["RemoteTask"]

# Set module to simulate it's not available locally
RemoteTask.__module__ = "remote.distributed.system"

# Create and serialize a task instance
task = RemoteTask(
    task_id="TASK_001",
    name="Process Data Pipeline",
    priority=5,
    payload={"input_file": "data.csv", "output_format": "parquet"}
)

# Serialize the task
json_str = kajson.dumps(task)
print(f"Serialized: {json_str[:100]}...")

# Clear the local class definition (simulate distributed scenario)
del remote_namespace["RemoteTask"]

# Without registry, deserialization fails
try:
    kajson.loads(json_str)
except KajsonDecoderError as e:
    print(f"Expected failure: {e}")

# Register the class in the registry
registry = KajsonManager.get_class_registry()
registry.register_class(RemoteTask)

# Now deserialization works!
restored_task = kajson.loads(json_str)
print(f"Restored: {restored_task.get_info()}")
print(f"Payload: {restored_task.payload}")

# Clean up
registry.teardown()
```

## Advanced Usage

### Custom Registry Implementation

You can create a custom registry by implementing the `ClassRegistryAbstract` interface:

```python
from kajson.class_registry_abstract import ClassRegistryAbstract
from typing import Type, Any, Optional, Dict, List
from pydantic import BaseModel

class CustomRegistry(ClassRegistryAbstract):
    def __init__(self):
        self._classes: Dict[str, Type[Any]] = {}
    
    def setup(self) -> None:
        """Initialize the registry."""
        pass
    
    def teardown(self) -> None:
        """Clear all registered classes."""
        self._classes.clear()
    
    def register_class(
        self,
        class_type: Type[Any],
        name: Optional[str] = None,
        should_warn_if_already_registered: bool = True
    ) -> None:
        """Register a single class."""
        key = name or class_type.__name__
        self._classes[key] = class_type
    
    # Implement other required methods...
```

### Using with Microservices

Example of using the class registry in a microservices architecture:

```python
# Service A - Defines models
class OrderModel(BaseModel):
    order_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    total: float

# Service B - Receives serialized orders
def process_order(order_json: str):
    # Register the model from Service A
    registry = KajsonManager.get_class_registry()
    registry.register_class(OrderModel)
    
    # Deserialize the order
    order = kajson.loads(order_json)
    
    # Process the order
    print(f"Processing order {order.order_id} for customer {order.customer_id}")
    print(f"Total: ${order.total}")
```

### Plugin System Example

```python
# Plugin system that loads classes dynamically
class PluginRegistry:
    def __init__(self):
        self.kajson_registry = KajsonManager.get_class_registry()
    
    def load_plugin(self, plugin_code: str, plugin_name: str):
        # Execute plugin code to get classes
        plugin_namespace = {}
        exec(plugin_code, plugin_namespace)
        
        # Register all BaseModel classes from the plugin
        for name, obj in plugin_namespace.items():
            if isinstance(obj, type) and issubclass(obj, BaseModel):
                # Ensure unique module name for the plugin
                obj.__module__ = f"plugins.{plugin_name}"
                self.kajson_registry.register_class(obj, f"{plugin_name}.{name}")
    
    def serialize_plugin_data(self, data: BaseModel) -> str:
        return kajson.dumps(data)
    
    def deserialize_plugin_data(self, json_str: str) -> BaseModel:
        # The registry will handle finding the right class
        return kajson.loads(json_str)
```

## Best Practices

1. **Clear Naming**: Use descriptive names when registering classes to avoid conflicts
2. **Module Simulation**: Set meaningful `__module__` values for dynamic classes
3. **Cleanup**: Use `teardown()` to clear registrations when appropriate
4. **Error Handling**: Always handle `KajsonDecoderError` when deserializing
5. **Type Safety**: Use `get_required_subclass()` to ensure type safety

## Error Handling

The class registry raises specific exceptions:

- `ClassRegistryNotFoundError`: When a required class is not found
- `ClassRegistryInheritanceError`: When a class doesn't match expected inheritance

## Integration with kajson

The class registry is automatically checked during deserialization:

1. kajson first checks if the module is already imported
2. If not found, it checks the class registry
3. If still not found, it attempts to import the module
4. If import fails, a `KajsonDecoderError` is raised

This seamless integration means you only need to register your classes once, and kajson handles the rest automatically.

## See Also

- [Basic Usage Guide](basic-usage.md) - Learn the fundamentals of kajson
- [Custom Types Guide](custom-types.md) - Handle custom types with encoders/decoders
- [API Reference](../api/kajson.md) - Complete API documentation
- [Example: Dynamic Class Registry](https://github.com/PipelexLab/kajson/blob/main/examples/ex_14_dynamic_class_registry.py) - Full working example
