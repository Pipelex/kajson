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
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from kajson import kajson, kajson_manager
from kajson.exceptions import KajsonDecoderError
from kajson.kajson_manager import KajsonManager


def main():
    print("=== Dynamic Class Registry Example ===\n")

    # Simulate receiving a class definition from a remote system
    print("📡 Simulating dynamic class creation (e.g., from network, workflow definition, etc.)")

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
    print("🏗️  Creating class from remote definition...")

    remote_namespace: Dict[str, Any] = {}
    exec(remote_class_definition, remote_namespace)
    RemoteTask = remote_namespace["RemoteTask"]

    # Set module to simulate it's not available locally
    RemoteTask.__module__ = "remote.distributed.system"

    # Rebuild the model
    types_namespace = {"Optional": Optional, "Dict": Dict, "Any": Any, "BaseModel": BaseModel, "Field": Field}
    RemoteTask.model_rebuild(_types_namespace=types_namespace)

    # Create and serialize a task instance
    task = RemoteTask(task_id="TASK_001", name="Process Data Pipeline", priority=5, payload={"input_file": "data.csv", "output_format": "parquet"})

    print(f"📋 Created task: {task.get_info()}")
    print(f"   Task type: {type(task)}")
    print(f"   Task module: {task.__class__.__module__}")

    # Serialize the task
    json_str = kajson.dumps(task)
    print(f"\n📤 Serialized task to JSON ({len(json_str)} chars)")
    print(f"   JSON preview: {json_str[:100]}...")

    # Clear the local class definition (simulate it's no longer available)
    print("\n🗑️  Clearing local class definition (simulating distributed scenario)")
    del remote_namespace["RemoteTask"]

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
    print("   • Distributed systems with class definitions over network")
    print("   • Workflow orchestrators with dynamic task types")
    print("   • Plugin systems with runtime-loaded classes")
    print("   • Microservices exchanging complex object definitions")
    print("   • Any scenario where classes aren't in standard module paths")

    # Clean up
    registry.teardown()


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
