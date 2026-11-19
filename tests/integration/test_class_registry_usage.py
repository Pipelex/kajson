# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""
Tests demonstrating when the class registry is actually needed during deserialization.

These tests simulate scenarios where classes need to be available for deserialization
but are not in the standard module path (e.g., distributed systems, dynamic class generation).
The dynamic classes are built with pydantic's create_model: kajson never executes code.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import pytest
from pydantic import BaseModel, Field, create_model, field_validator

from kajson import kajson
from kajson.exceptions import KajsonDecoderError
from kajson.kajson_manager import KajsonManager


class _MessageBehaviour(BaseModel):
    """Behaviour shared by the dynamically built message classes: a validator and a method."""

    @field_validator("recipients", check_fields=False)
    @classmethod
    def validate_recipients(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one recipient is required")
        return v

    def get_summary(self) -> str:
        fields = self.model_dump()
        return f"Message {fields['message_id']} from {fields['sender']} to {len(fields['recipients'])} recipients"


class TestClassRegistryUsage:
    """Tests demonstrating actual usage of the class registry during deserialization."""

    def test_dynamic_basemodel_requires_registry(self):
        """Test that dynamically created BaseModel requires class registry for deserialization."""

        # Build a BaseModel at runtime with create_model (simulates runtime class generation),
        # giving it a module that does not exist so kajson cannot import it by name
        DynamicProduct = create_model(
            "DynamicProduct",
            __module__="test.fake.module",
            id=(int, Field(..., description="Product ID")),
            name=(str, Field(..., description="Product name")),
            price=(float, Field(..., gt=0, description="Product price")),
            category=(Optional[str], Field(None, description="Product category")),
        )

        # Create an instance of the dynamic class
        product = DynamicProduct(id=123, name="Super Widget", price=29.99, category="Electronics")

        print(f"Created dynamic product: {product}")
        print(f"Product type: {type(product)}")
        print(f"Product module: {product.__class__.__module__}")

        # Serialize the instance
        json_str = kajson.dumps(product)
        print(f"Serialized JSON: {json_str}")

        # Without registry registration, deserialization fails: the module cannot be imported
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

    def test_class_registry_with_class_built_from_field_definitions(self):
        """Test class registry with a class built from field definitions received as data."""

        # The class description arrives as data (simulates receiving it over the network),
        # never as code: the receiving side turns it into a class itself
        received_fields: Dict[str, Any] = {
            "message_id": (str, Field(..., description="Unique message identifier")),
            "sender": (str, Field(..., min_length=1, description="Sender identifier")),
            "recipients": (List[str], Field(..., min_length=1, description="List of recipients")),
            "subject": (str, Field(..., description="Message subject")),
            "body": (str, Field(..., description="Message body")),
            "timestamp": (Optional[datetime], Field(default=None, description="Message timestamp")),
            "priority": (int, Field(default=1, ge=1, le=5, description="Message priority (1-5)")),
        }

        # Behaviour (methods, validators) comes from a base class the receiver already has
        # A class built at runtime has no static type, so the type checker sees it as Any
        NetworkMessage: Any = create_model(
            "NetworkMessage",
            __base__=_MessageBehaviour,
            __module__="test.fake.module",
            **received_fields,
        )

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
            assert restored_message.timestamp == datetime(2025, 1, 15, 14, 30, 0)
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
