#!/usr/bin/env python3
"""
Pydantic Subclass Polymorphism Example

This example demonstrates how Kajson perfectly handles polymorphism with Pydantic models:
- A field is declared with a base class type (e.g., Animal)
- The actual instance is a subclass of that base class (e.g., Dog, Cat)
- Deserialization correctly reconstructs the specific subclass instance
- All subclass-specific attributes and methods are preserved
"""

from typing import Dict, List

from pydantic import BaseModel, Field
from typing_extensions import override

from kajson import kajson, kajson_manager


class Animal(BaseModel):
    """Base animal class with common attributes."""

    name: str
    species: str
    age: int

    def make_sound(self) -> str:
        return "Some generic animal sound"

    def get_description(self) -> str:
        return f"{self.name} is a {self.age}-year-old {self.species}"


class Dog(Animal):
    """Dog subclass with breed-specific attributes."""

    breed: str
    is_good_boy: bool = True
    favorite_toy: str = "tennis ball"

    @override
    def make_sound(self) -> str:
        return "Woof! Woof!"

    @override
    def get_description(self) -> str:
        return f"{super().get_description()} ({self.breed} breed)"


class Cat(Animal):
    """Cat subclass with feline-specific attributes."""

    lives_remaining: int = 9
    is_indoor: bool = True
    favorite_nap_spot: str = "sunny windowsill"

    @override
    def make_sound(self) -> str:
        return "Meow~"

    @override
    def get_description(self) -> str:
        indoor_status = "indoor" if self.is_indoor else "outdoor"
        return f"{super().get_description()} ({indoor_status} cat with {self.lives_remaining} lives)"


class Bird(Animal):
    """Bird subclass with avian-specific attributes."""

    can_fly: bool = True
    wingspan_cm: float = Field(gt=0)
    migration_distance_km: int = 0

    @override
    def make_sound(self) -> str:
        return "Tweet tweet!"

    @override
    def get_description(self) -> str:
        flight_status = "flying" if self.can_fly else "flightless"
        return f"{super().get_description()} ({flight_status} bird, {self.wingspan_cm}cm wingspan)"


class Pet(BaseModel):
    """Pet registration with owner information."""

    owner_name: str
    animal: Animal  # ← Field declared as base class, but can hold subclass instances
    registration_date: str
    veterinarian: str

    def get_summary(self) -> str:
        return f"{self.owner_name}'s pet: {self.animal.get_description()}"


class AnimalShelter(BaseModel):
    """Animal shelter with mixed animal types."""

    name: str
    location: str
    animals: List[Animal]  # ← List of base class, but can contain subclass instances
    capacity: int

    def get_animal_count_by_type(self) -> Dict[str, int]:
        """Count animals by their actual subclass type."""
        counts: Dict[str, int] = {}
        for animal in self.animals:
            animal_type = type(animal).__name__
            counts[animal_type] = counts.get(animal_type, 0) + 1
        return counts


def main():
    print("=== Pydantic Subclass Polymorphism Example ===\n")

    # Create pets with different animal subclasses
    pets = [
        Pet(
            owner_name="Alice Smith",
            animal=Dog(name="Buddy", species="Canis lupus familiaris", age=3, breed="Golden Retriever", is_good_boy=True, favorite_toy="frisbee"),
            registration_date="2024-01-15",
            veterinarian="Dr. Johnson",
        ),
        Pet(
            owner_name="Bob Wilson",
            animal=Cat(name="Whiskers", species="Felis catus", age=5, lives_remaining=8, is_indoor=True, favorite_nap_spot="cardboard box"),
            registration_date="2024-02-20",
            veterinarian="Dr. Martinez",
        ),
        Pet(
            owner_name="Carol Davis",
            animal=Bird(name="Sunny", species="Canarius canarius", age=2, can_fly=True, wingspan_cm=15.5, migration_distance_km=0),
            registration_date="2024-03-10",
            veterinarian="Dr. Thompson",
        ),
    ]

    print("🐾 Original Pets:")
    for i, pet in enumerate(pets, 1):
        print(f"  {i}. {pet.get_summary()}")
        print(f"     Type: {type(pet.animal).__name__}")
        print(f"     Sound: {pet.animal.make_sound()}")
        print()

    # Create an animal shelter with mixed types
    shelter = AnimalShelter(
        name="Happy Paws Animal Shelter",
        location="Springfield",
        capacity=50,
        animals=[
            Dog(name="Max", species="Canis lupus", age=4, breed="German Shepherd", favorite_toy="rope"),
            Cat(name="Luna", species="Felis catus", age=2, lives_remaining=9, favorite_nap_spot="cat tower"),
            Bird(name="Charlie", species="Psittacus erithacus", age=8, wingspan_cm=65.0, can_fly=False),
            Dog(name="Bella", species="Canis lupus", age=1, breed="Labrador", is_good_boy=True),
            Cat(name="Shadow", species="Felis catus", age=6, is_indoor=False, lives_remaining=7),
        ],
    )

    print(f"🏠 Original Shelter: {shelter.name}")
    print(f"   Location: {shelter.location}")
    print(f"   Animal counts: {shelter.get_animal_count_by_type()}")
    print()

    # Serialize everything
    pets_json = kajson.dumps(pets, indent=2)
    shelter_json = kajson.dumps(shelter, indent=2)

    print("📦 Serialization completed")
    print(f"   Pets JSON size: {len(pets_json)} characters")
    print(f"   Shelter JSON size: {len(shelter_json)} characters")
    print()

    # Deserialize and verify subclass types are preserved
    restored_pets = kajson.loads(pets_json)
    restored_shelter = kajson.loads(shelter_json)

    print("📦 Deserialization completed - verifying subclass preservation...")
    print()

    print("🔍 Restored Pets:")
    for i, pet in enumerate(restored_pets, 1):
        original_pet = pets[i - 1]
        print(f"  {i}. {pet.get_summary()}")
        print(f"     Type: {type(pet.animal).__name__}")
        print(f"     Sound: {pet.animal.make_sound()}")

        # Verify the subclass type is preserved
        assert type(pet.animal) is type(original_pet.animal)

        # Verify subclass-specific attributes
        if isinstance(pet.animal, Dog) and isinstance(original_pet.animal, Dog):
            assert pet.animal.breed == original_pet.animal.breed
            assert pet.animal.favorite_toy == original_pet.animal.favorite_toy
            print(f"     ✅ Dog-specific: breed={pet.animal.breed}, toy={pet.animal.favorite_toy}")
        elif isinstance(pet.animal, Cat) and isinstance(original_pet.animal, Cat):
            assert pet.animal.lives_remaining == original_pet.animal.lives_remaining
            assert pet.animal.favorite_nap_spot == original_pet.animal.favorite_nap_spot
            print(f"     ✅ Cat-specific: lives={pet.animal.lives_remaining}, nap_spot={pet.animal.favorite_nap_spot}")
        elif isinstance(pet.animal, Bird) and isinstance(original_pet.animal, Bird):
            assert pet.animal.wingspan_cm == original_pet.animal.wingspan_cm
            assert pet.animal.can_fly == original_pet.animal.can_fly
            print(f"     ✅ Bird-specific: wingspan={pet.animal.wingspan_cm}cm, can_fly={pet.animal.can_fly}")
        print()

    print(f"🔍 Restored Shelter: {restored_shelter.name}")
    print(f"   Location: {restored_shelter.location}")
    print(f"   Animal counts: {restored_shelter.get_animal_count_by_type()}")

    # Verify shelter animals preserved their types
    assert len(restored_shelter.animals) == len(shelter.animals)
    for original, restored in zip(shelter.animals, restored_shelter.animals):
        assert type(original) is type(restored)
        assert original.name == restored.name
        assert original.age == restored.age

    print("   ✅ All shelter animals preserved their subclass types!")
    print()

    print("🎉 SUCCESS: All subclass polymorphism tests passed!")
    print("   • Base class field declarations work correctly")
    print("   • Subclass instances are preserved during serialization")
    print("   • All subclass-specific attributes and methods are maintained")
    print("   • Works with both single instances and lists of mixed types")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
