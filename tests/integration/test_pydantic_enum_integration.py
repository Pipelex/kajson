"""Integration tests for enum serialization within Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

import pytest
from pydantic import BaseModel

from kajson import kajson


class Personality(Enum):
    """Pet personality enum - matches hello_2.py."""

    PLAYFUL = "playful"
    GRUMPY = "grumpy"
    CUDDLY = "cuddly"
    SHY = "shy"
    ENERGETIC = "energetic"


class Priority(Enum):
    """Task priority enum."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class Status(Enum):
    """Status enum with string values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Pydantic models - similar to hello_2.py pattern
class Animal(BaseModel):
    """Base animal model."""

    name: str


class Dog(Animal):
    """Dog model with breed."""

    breed: str


class Cat(Animal):
    """Cat model with personality enum - matches hello_2.py."""

    indoor: bool
    personality: Personality


class Pet(BaseModel):
    """Pet model with polymorphic animal field - matches hello_2.py."""

    acquired: datetime
    animal: Animal


class Task(BaseModel):
    """Task model with multiple enums."""

    title: str
    status: Status
    priority: Priority
    due_date: Optional[datetime] = None


class Project(BaseModel):
    """Project model containing lists of enum-containing models."""

    name: str
    tasks: List[Task]
    lead_pets: List[Pet]  # Pets belonging to project leads


class PersonalityProfile(BaseModel):
    """Profile model with list of personality enums."""

    pet_name: str
    possible_personalities: List[Personality]


class TestPydanticEnumIntegration:
    """Test enum integration with Pydantic models."""

    def test_single_enum_in_pydantic_model(self):
        """Test single enum field in Pydantic model - hello_2.py pattern."""
        # Create a cat with personality enum
        cat = Cat(name="Whiskers", indoor=True, personality=Personality.GRUMPY)

        # Serialize and deserialize
        json_str = kajson.dumps(cat)
        restored_cat = kajson.loads(json_str)

        # Verify type and values
        assert isinstance(restored_cat, Cat)
        assert restored_cat.name == "Whiskers"
        assert restored_cat.indoor is True
        assert isinstance(restored_cat.personality, Personality)
        assert restored_cat.personality == Personality.GRUMPY
        assert restored_cat.personality.value == "grumpy"

    def test_polymorphic_model_with_enum(self):
        """Test polymorphic Pydantic model containing enum - exact hello_2.py pattern."""
        # Create instances with different subclasses (matches hello_2.py)
        fido = Pet(acquired=datetime.now(), animal=Dog(name="Fido", breed="Corgi"))
        whiskers = Pet(acquired=datetime.now(), animal=Cat(name="Whiskers", indoor=True, personality=Personality.GRUMPY))

        # Test the Dog pet (no enum)
        fido_json = kajson.dumps(fido)
        fido_restored = kajson.loads(fido_json)

        assert isinstance(fido_restored, Pet)
        assert isinstance(fido_restored.animal, Dog)
        assert fido_restored.animal.name == "Fido"
        assert fido_restored.animal.breed == "Corgi"

        # Test the Cat pet (with enum) - main hello_2.py test case
        whiskers_json = kajson.dumps(whiskers)
        whiskers_restored = kajson.loads(whiskers_json)

        # Verify exact hello_2.py assertions
        assert isinstance(whiskers_restored.animal, Cat)  # ✓ Still a Cat, not just Animal
        assert whiskers_restored.animal.personality == Personality.GRUMPY  # ✓ Enum preserved
        assert whiskers_restored.animal.indoor is True  # ✓ All attributes intact

    def test_multiple_enums_in_single_model(self):
        """Test model with multiple enum fields."""
        task = Task(title="Fix bug", status=Status.IN_PROGRESS, priority=Priority.HIGH, due_date=datetime.now())

        # Serialize and deserialize
        json_str = kajson.dumps(task)
        restored_task = kajson.loads(json_str)

        # Verify
        assert isinstance(restored_task, Task)
        assert restored_task.title == "Fix bug"
        assert isinstance(restored_task.status, Status)
        assert restored_task.status == Status.IN_PROGRESS
        assert isinstance(restored_task.priority, Priority)
        assert restored_task.priority == Priority.HIGH
        assert isinstance(restored_task.due_date, datetime)

    def test_nested_models_with_enums(self):
        """Test complex nested structure with multiple enum-containing models."""
        # Create tasks with different enum values
        tasks = [
            Task(title="Design API", status=Status.COMPLETED, priority=Priority.HIGH),
            Task(title="Write tests", status=Status.IN_PROGRESS, priority=Priority.MEDIUM),
            Task(title="Deploy", status=Status.PENDING, priority=Priority.URGENT),
        ]

        # Create pets with enum personalities
        pets = [
            Pet(acquired=datetime.now(), animal=Cat(name="Shadow", indoor=False, personality=Personality.SHY)),
            Pet(acquired=datetime.now(), animal=Cat(name="Fluffy", indoor=True, personality=Personality.CUDDLY)),
        ]

        # Create project with nested enum-containing models
        project = Project(name="Web App", tasks=tasks, lead_pets=pets)

        # Serialize and deserialize
        json_str = kajson.dumps(project)
        restored_project = kajson.loads(json_str)

        # Verify project structure
        assert isinstance(restored_project, Project)
        assert restored_project.name == "Web App"
        assert len(restored_project.tasks) == 3
        assert len(restored_project.lead_pets) == 2

        # Verify task enums
        for original_task, restored_task in zip(tasks, restored_project.tasks):
            assert isinstance(restored_task, Task)
            assert isinstance(restored_task.status, Status)
            assert isinstance(restored_task.priority, Priority)
            assert restored_task.status == original_task.status
            assert restored_task.priority == original_task.priority

        # Verify pet enums
        for restored_pet in restored_project.lead_pets:
            assert isinstance(restored_pet, Pet)
            assert isinstance(restored_pet.animal, Cat)
            assert isinstance(restored_pet.animal.personality, Personality)

        # Verify specific enum values
        assert restored_project.tasks[0].status == Status.COMPLETED
        assert restored_project.tasks[1].status == Status.IN_PROGRESS
        assert restored_project.tasks[2].status == Status.PENDING

        # Cast to Cat for personality access
        pet0_animal = restored_project.lead_pets[0].animal
        pet1_animal = restored_project.lead_pets[1].animal
        assert isinstance(pet0_animal, Cat)
        assert isinstance(pet1_animal, Cat)
        assert pet0_animal.personality == Personality.SHY
        assert pet1_animal.personality == Personality.CUDDLY

    def test_enum_in_list_within_pydantic(self):
        """Test list of enums within Pydantic model."""
        profile = PersonalityProfile(pet_name="Multi-faceted Cat", possible_personalities=[Personality.PLAYFUL, Personality.CUDDLY, Personality.SHY])

        # Serialize and deserialize
        json_str = kajson.dumps(profile)
        restored_profile = kajson.loads(json_str)

        # Verify
        assert isinstance(restored_profile, PersonalityProfile)
        assert restored_profile.pet_name == "Multi-faceted Cat"
        assert len(restored_profile.possible_personalities) == 3

        for personality in restored_profile.possible_personalities:
            assert isinstance(personality, Personality)

        assert Personality.PLAYFUL in restored_profile.possible_personalities
        assert Personality.CUDDLY in restored_profile.possible_personalities
        assert Personality.SHY in restored_profile.possible_personalities

    def test_all_personality_enum_values(self):
        """Test that all personality enum values work correctly in Pydantic models."""
        for personality in Personality:
            cat = Cat(name=f"Cat_{personality.name}", indoor=True, personality=personality)

            # Serialize and deserialize
            json_str = kajson.dumps(cat)
            restored_cat = kajson.loads(json_str)

            # Verify
            assert isinstance(restored_cat, Cat)
            assert isinstance(restored_cat.personality, Personality)
            assert restored_cat.personality == personality
            assert restored_cat.personality.value == personality.value

    def test_enum_inheritance_with_pydantic(self):
        """Test that enum types are preserved with Pydantic model inheritance."""
        # Test with different animal types
        animals = [Dog(name="Rex", breed="German Shepherd"), Cat(name="Mittens", indoor=True, personality=Personality.ENERGETIC)]

        for animal in animals:
            # Serialize and deserialize
            json_str = kajson.dumps(animal)
            restored_animal = kajson.loads(json_str)

            # Verify type preservation
            assert type(restored_animal) is type(animal)
            assert restored_animal.name == animal.name

            # Verify enum preservation for cats
            if isinstance(animal, Cat):
                assert isinstance(restored_animal, Cat)
                cat_animal = animal
                cat_restored = restored_animal
                assert isinstance(cat_restored.personality, Personality)
                assert cat_restored.personality == cat_animal.personality


class TestPydanticEnumErrorHandling:
    """Test error handling for enum integration with Pydantic."""

    def test_invalid_enum_value_in_pydantic(self):
        """Test that invalid enum values are handled appropriately."""
        # This should raise a validation error during model creation
        with pytest.raises(ValueError):  # Pydantic validation error
            Cat(name="Invalid Cat", indoor=True, personality="invalid_personality")  # type: ignore

    def test_pydantic_model_with_corrupted_enum_data(self):
        """Test deserialization of Pydantic model with corrupted enum data."""
        # Create valid cat first
        cat = Cat(name="Test Cat", indoor=True, personality=Personality.PLAYFUL)
        json_str = kajson.dumps(cat)

        # Corrupt the enum data by replacing the enum value
        corrupted_json = json_str.replace('"PLAYFUL"', '"INVALID_PERSONALITY"')

        # Attempt to deserialize - should handle gracefully
        with pytest.raises(Exception):  # Could be KeyError, ValueError, or KajsonDecoderError
            kajson.loads(corrupted_json)
