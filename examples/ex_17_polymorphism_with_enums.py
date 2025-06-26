#!/usr/bin/env python3
"""
Polymorphism with Enums Example

This example demonstrates how Kajson perfectly handles polymorphism with Pydantic models
that include enum fields. It shows that:
- A field can be declared with a base class type (e.g., Animal)
- The actual instance can be a subclass with enum fields (e.g., Cat with Personality enum)
- Deserialization correctly reconstructs the specific subclass instance
- Enum values are perfectly preserved during serialization/deserialization
- All subclass-specific attributes and enum fields are maintained
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from typing_extensions import override

from kajson import kajson, kajson_manager


class Personality(Enum):
    """Enum representing different cat personalities."""

    PLAYFUL = "playful"
    GRUMPY = "grumpy"
    CUDDLY = "cuddly"


class Animal(BaseModel):
    """Base animal class with common attributes."""

    name: str

    def get_description(self) -> str:
        return f"Animal named {self.name}"


class Dog(Animal):
    """Dog subclass with breed-specific attributes."""

    breed: str

    @override
    def get_description(self) -> str:
        return f"Dog named {self.name} ({self.breed} breed)"


class Cat(Animal):
    """Cat subclass with feline-specific attributes including personality enum."""

    indoor: bool
    personality: Personality

    @override
    def get_description(self) -> str:
        indoor_status = "indoor" if self.indoor else "outdoor"
        return f"Cat named {self.name} ({indoor_status}, {self.personality.value} personality)"


class Pet(BaseModel):
    """Pet registration with acquisition date and animal reference."""

    acquired: datetime
    animal: Animal  # ← Field declared as base class, but can hold subclass instances

    def get_summary(self) -> str:
        return f"Pet acquired on {self.acquired.strftime('%Y-%m-%d')}: {self.animal.get_description()}"


def main():
    print("=== Polymorphism with Enums Example ===\n")

    # Create instances with different subclasses
    fido = Pet(acquired=datetime.now(), animal=Dog(name="Fido", breed="Corgi"))

    whiskers = Pet(acquired=datetime.now(), animal=Cat(name="Whiskers", indoor=True, personality=Personality.GRUMPY))

    print("🐾 Original Pets:")
    print(f"  1. {fido.get_summary()}")
    print(f"     Type: {type(fido.animal).__name__}")
    if isinstance(fido.animal, Dog):
        print(f"     Dog-specific: breed={fido.animal.breed}")
    print()

    print(f"  2. {whiskers.get_summary()}")
    print(f"     Type: {type(whiskers.animal).__name__}")
    if isinstance(whiskers.animal, Cat):
        print(f"     Cat-specific: indoor={whiskers.animal.indoor}, personality={whiskers.animal.personality}")
    print()

    # Serialize to JSON
    fido_json = kajson.dumps(fido, indent=2)
    whiskers_json = kajson.dumps(whiskers, indent=2)

    print("📦 Serialization completed")
    print(f"  Fido JSON size: {len(fido_json)} characters")
    print(f"  Whiskers JSON size: {len(whiskers_json)} characters")
    print()

    print("📄 Serialized JSON for Whiskers:")
    print(whiskers_json)
    print()

    # Deserialize back
    fido_restored = kajson.loads(fido_json)
    whiskers_restored = kajson.loads(whiskers_json)

    print("📦 Deserialization completed - verifying subclass and enum preservation...")
    print()

    print("🔍 Restored Pets:")
    print(f"  1. {fido_restored.get_summary()}")
    print(f"     Type: {type(fido_restored.animal).__name__}")
    print(f"     Dog-specific: breed={fido_restored.animal.breed}")

    # Verify Dog subclass preservation
    assert isinstance(fido_restored.animal, Dog)
    # We know fido.animal is a Dog from the original creation
    fido_dog = fido.animal  # type: ignore[assignment]
    assert isinstance(fido_dog, Dog)
    assert fido_restored.animal.breed == fido_dog.breed
    print("     ✅ Dog subclass and attributes preserved!")
    print()

    print(f"  2. {whiskers_restored.get_summary()}")
    print(f"     Type: {type(whiskers_restored.animal).__name__}")
    print(f"     Cat-specific: indoor={whiskers_restored.animal.indoor}, personality={whiskers_restored.animal.personality}")

    # Verify Cat subclass and enum preservation
    assert isinstance(whiskers_restored.animal, Cat)
    # We know whiskers.animal is a Cat from the original creation
    assert whiskers_restored.animal.personality == Personality.GRUMPY
    assert whiskers_restored.animal.indoor is True
    print("     ✅ Cat subclass and enum values preserved!")
    print()

    # Additional verification
    print("🔍 Additional Verification:")
    print(f"  • Fido type preserved: {isinstance(fido_restored.animal, Dog)}")  # pyright: ignore[reportUnnecessaryIsInstance]
    print(f"  • Whiskers type preserved: {isinstance(whiskers_restored.animal, Cat)}")  # pyright: ignore[reportUnnecessaryIsInstance]
    print(f"  • Enum value preserved: {whiskers_restored.animal.personality == Personality.GRUMPY}")
    print(f"  • Enum type preserved: {type(whiskers_restored.animal.personality) is Personality}")
    print(f"  • All attributes intact: {whiskers_restored.animal.indoor is True}")
    print()

    print("🎉 SUCCESS: All polymorphism and enum tests passed!")
    print("   • Base class field declarations work correctly")
    print("   • Subclass instances are preserved during serialization")
    print("   • Enum values are perfectly maintained")
    print("   • All subclass-specific attributes are intact")
    print("   • Perfect reconstruction of complex nested structures")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
