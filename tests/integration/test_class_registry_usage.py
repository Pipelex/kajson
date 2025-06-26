# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""
Tests demonstrating when the class registry is actually needed during deserialization.

These tests simulate scenarios where classes need to be available for deserialization
but are not in the standard module path (e.g., distributed systems, dynamic class generation).
"""

from __future__ import annotations

from typing import Any, Dict

import pytest
from pydantic import BaseModel, Field

from kajson import kajson
from kajson.exceptions import KajsonDecoderError
from kajson.kajson_manager import KajsonManager


class TestClassRegistryUsage:
    """Tests demonstrating actual usage of the class registry during deserialization."""

    def test_dynamic_basemodel_requires_registry(self):
        """Test that dynamically created BaseModel requires class registry for deserialization."""

        # Create a BaseModel dynamically using exec (simulates runtime class generation)
        dynamic_class_code = '''
from pydantic import BaseModel, Field
from typing import Optional

class DynamicProduct(BaseModel):
    """A dynamically created product model."""
    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Product name") 
    price: float = Field(..., gt=0, description="Product price")
    category: Optional[str] = Field(None, description="Product category")
    
    def __str__(self) -> str:
        return f"DynamicProduct(id={self.id}, name='{self.name}', price={self.price})"
'''

        # Create a namespace and execute the dynamic class
        dynamic_namespace: Dict[str, Any] = {}
        exec(dynamic_class_code, dynamic_namespace)
        DynamicProduct = dynamic_namespace["DynamicProduct"]

        # Set the module to something that doesn't exist to force registry lookup
        DynamicProduct.__module__ = "test.fake.module"

        # Rebuild the model to resolve forward references with proper types namespace
        from typing import Optional

        from pydantic import BaseModel

        types_namespace = {"Optional": Optional, "BaseModel": BaseModel, "Field": Field}
        DynamicProduct.model_rebuild(_types_namespace=types_namespace)

        # Create an instance of the dynamic class
        product = DynamicProduct(id=123, name="Super Widget", price=29.99, category="Electronics")

        print(f"Created dynamic product: {product}")
        print(f"Product type: {type(product)}")
        print(f"Product module: {product.__class__.__module__}")

        # Serialize the instance
        json_str = kajson.dumps(product)
        print(f"Serialized JSON: {json_str}")

        # Now simulate the scenario where the class is not available in sys.modules
        # but we have it registered in the class registry

        # First, let's see what happens without registry - should fail
        # Remove the class from the local namespace to simulate it not being available
        del dynamic_namespace["DynamicProduct"]

        # Try to deserialize without registry registration - should fail
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(json_str)

        assert "Error while trying to import module" in str(excinfo.value)
        print(f"✅ Without registry registration, deserialization fails as expected: {excinfo.value}")

        # Now register the class in the registry
        registry = KajsonManager.get_class_registry()
        registry.register_class(DynamicProduct)
        print("✅ Registered DynamicProduct in class registry")

        try:
            # Now deserialization should work via the class registry
            restored_product = kajson.loads(json_str)
            print(f"Restored product: {restored_product}")
            print(f"Restored type: {type(restored_product)}")

            # Verify the restoration worked correctly
            assert restored_product.id == 123
            assert restored_product.name == "Super Widget"
            assert restored_product.price == 29.99
            assert restored_product.category == "Electronics"
            assert isinstance(restored_product, DynamicProduct)

            print("✅ Class registry enabled successful deserialization of dynamic class!")
        finally:
            # Clean up registry for other tests
            registry.teardown()

    def test_class_registry_with_string_source_code(self):
        """Test class registry with a class defined entirely from string source code."""

        # Define a BaseModel entirely as a string (simulates receiving class definition over network)
        model_source = '''
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

class NetworkMessage(BaseModel):
    """A message received over network with dynamic class definition."""
    
    message_id: str = Field(..., description="Unique message identifier")
    sender: str = Field(..., min_length=1, description="Sender identifier")
    recipients: List[str] = Field(..., min_length=1, description="List of recipients")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message body")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")
    priority: int = Field(default=1, ge=1, le=5, description="Message priority (1-5)")
    
    @field_validator('recipients')
    @classmethod
    def validate_recipients(cls, v):
        if not v:
            raise ValueError('At least one recipient is required')
        return v
    
    def get_summary(self) -> str:
        return f"Message {self.message_id} from {self.sender} to {len(self.recipients)} recipients"
'''

        # Execute the string to create the class
        network_namespace: Dict[str, Any] = {}
        exec(model_source, network_namespace)
        NetworkMessage = network_namespace["NetworkMessage"]

        # Set the module to something that doesn't exist to force registry lookup
        NetworkMessage.__module__ = "test.fake.module"

        # Rebuild the model to resolve forward references with proper types namespace
        from datetime import datetime
        from typing import List, Optional

        from pydantic import BaseModel, Field, field_validator

        types_namespace = {
            "List": List,
            "Optional": Optional,
            "datetime": datetime,
            "BaseModel": BaseModel,
            "Field": Field,
            "field_validator": field_validator,
        }
        NetworkMessage.model_rebuild(_types_namespace=types_namespace)

        # Create an instance
        message = NetworkMessage(
            message_id="msg_001",
            sender="alice@example.com",
            recipients=["bob@example.com", "charlie@example.com"],
            subject="Project Update",
            body="The project is progressing well...",
            timestamp=datetime(2025, 1, 15, 14, 30, 0),
            priority=3,
        )

        print(f"Created network message: {message.get_summary()}")

        # Serialize
        json_str = kajson.dumps(message)
        print(f"Serialized message to JSON ({len(json_str)} chars)")

        # Clear the namespace (simulate the class definition not being available locally)
        del network_namespace["NetworkMessage"]

        # Register in class registry (simulates receiving class registration from network)
        registry = KajsonManager.get_class_registry()
        registry.register_class(NetworkMessage)
        print("✅ Registered NetworkMessage in class registry")

        try:
            # Deserialize using class registry
            restored_message = kajson.loads(json_str)
            print(f"Restored message: {restored_message.get_summary()}")

            # Verify restoration
            assert restored_message.message_id == "msg_001"
            assert restored_message.sender == "alice@example.com"
            assert len(restored_message.recipients) == 2
            assert restored_message.subject == "Project Update"
            assert restored_message.priority == 3
            assert isinstance(restored_message, NetworkMessage)

            print("✅ Successfully deserialized complex model via class registry!")
        finally:
            # Clean up
            registry.teardown()

    def test_registry_vs_module_import_precedence(self):
        """Test that class registry is checked before attempting module import."""

        # Create a class with a fake module name that doesn't exist
        class SpecialModel(BaseModel):
            value: str

        # Manually set the module to something that doesn't exist
        SpecialModel.__module__ = "test.fake.module"

        instance = SpecialModel(value="test")
        json_str = kajson.dumps(instance)

        # Without registry, this should fail with import error
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(json_str)
        assert "Error while trying to import module test.fake.module" in str(excinfo.value)

        # Register in class registry
        registry = KajsonManager.get_class_registry()
        registry.register_class(SpecialModel)

        try:
            # Now it should work via registry (bypassing the non-existent module)
            restored = kajson.loads(json_str)
            assert restored.value == "test"
            assert isinstance(restored, SpecialModel)

            print("✅ Class registry takes precedence over module import!")
        finally:
            # Clean up
            registry.teardown()
