#!/usr/bin/env python3
"""
Dynamic Class Registry Example

This example demonstrates when the class registry is essential for deserialization.
It shows scenarios where classes are created dynamically at runtime and need to be
available for deserialization, but aren't in the standard module path.

This is particularly useful for:
- Distributed systems where classes are defined dynamically
- Workflow orchestrators with dynamic task definitions
- Plugin systems with runtime class generation
- Microservices that exchange complex object definitions

kajson never executes code. A class description received from another system
arrives as data, and the receiving side builds the class itself, here with
pydantic's create_model, before registering it.
"""

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, create_model

from kajson import kajson, kajson_manager
from kajson.exceptions import KajsonDecoderError
from kajson.kajson_manager import KajsonManager


class TaskBehaviour(BaseModel):
    """Behaviour shared by every task class, defined in code the receiving side already has."""

    def get_info(self) -> str:
        fields = self.model_dump()
        return f"Task {fields['task_id']}: {fields['name']} (priority: {fields['priority']})"


# The receiving side decides which types a class description may use
FIELD_TYPES: Dict[str, Any] = {
    "string": str,
    "integer": int,
    "object": Optional[Dict[str, Any]],
}


def build_class(description: Dict[str, Any], module_name: str) -> Type[BaseModel]:
    """Build a pydantic class from a description received as data."""
    field_definitions: Dict[str, Any] = {}
    for field_name, field_spec in description["fields"].items():
        field_type = FIELD_TYPES[field_spec["type"]]
        default = field_spec.get("default", ...)
        field_definitions[field_name] = (field_type, Field(default, description=field_spec["description"]))
    return create_model(description["name"], __base__=TaskBehaviour, __module__=module_name, **field_definitions)


def main():
    print("=== Dynamic Class Registry Example ===\n")

    # Simulate receiving a class description from a remote system: data, never code
    print("📡 Simulating dynamic class creation (e.g., from network, workflow definition, etc.)")

    remote_class_description: Dict[str, Any] = {
        "name": "RemoteTask",
        "fields": {
            "task_id": {"type": "string", "description": "Unique task identifier"},
            "name": {"type": "string", "description": "Task name"},
            "priority": {"type": "integer", "default": 1, "description": "Task priority"},
            "payload": {"type": "object", "default": None, "description": "Task payload"},
        },
    }

    # Build the class, with a module that does not exist locally
    print("🏗️  Building class from remote description...")
    # A class built at runtime has no static type, so the type checker sees it as Any
    RemoteTask: Any = build_class(remote_class_description, module_name="remote.distributed.system")

    # Create and serialize a task instance
    task = RemoteTask(task_id="TASK_001", name="Process Data Pipeline", priority=5, payload={"input_file": "data.csv", "output_format": "parquet"})

    print(f"📋 Created task: {task.get_info()}")
    print(f"   Task type: {type(task)}")
    print(f"   Task module: {task.__class__.__module__}")

    # Serialize the task
    json_str = kajson.dumps(task)
    print(f"\n📤 Serialized task to JSON ({len(json_str)} chars)")
    print(f"   JSON preview: {json_str[:100]}...")

    # Try to deserialize without registry - should fail
    print("\n❌ Attempting deserialization without class registry...")
    try:
        kajson.loads(json_str)
        print("   Unexpected: Deserialization succeeded!")
    except KajsonDecoderError as e:
        print(f"   Expected failure: {e}")
        print("   This happens because the class module 'remote.distributed.system' doesn't exist")

    # Register the class in the registry
    print("\n🏛️  Registering class in kajson class registry...")
    registry = KajsonManager.get_class_registry()
    registry.register_class(RemoteTask)
    print("   ✅ RemoteTask registered successfully")

    # Now deserialization should work via the class registry
    print("\n✨ Attempting deserialization with class registry...")
    restored_task = kajson.loads(json_str)
    print(f"   ✅ Success! Restored: {restored_task.get_info()}")
    print(f"   Restored type: {type(restored_task)}")
    print(f"   Payload: {restored_task.payload}")

    # Verify the restoration
    assert restored_task.task_id == task.task_id
    assert restored_task.name == task.name
    assert restored_task.priority == task.priority
    assert restored_task.payload == task.payload
    assert isinstance(restored_task, RemoteTask)

    print("\n🎯 Perfect! Class registry enabled deserialization of dynamic class!")

    print("\n" + "=" * 60)
    print("📚 When do you need the class registry?")
    print("   • Dynamic class generation at runtime")
    print("   • Distributed systems with class descriptions over network")
    print("   • Workflow orchestrators with dynamic task types")
    print("   • Plugin systems with runtime-built classes")
    print("   • Microservices exchanging complex object definitions")
    print("   • Any scenario where classes aren't in standard module paths")

    # Clean up
    registry.teardown()


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
