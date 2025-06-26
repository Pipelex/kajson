from datetime import datetime
from enum import Enum

from pydantic import BaseModel

import kajson as json


# Define an enum
class Personality(Enum):
    PLAYFUL = "playful"
    GRUMPY = "grumpy"
    CUDDLY = "cuddly"


# Define a hierarchy with polymorphism
class Animal(BaseModel):
    name: str


class Dog(Animal):
    breed: str


class Cat(Animal):
    indoor: bool
    personality: Personality


class Pet(BaseModel):
    acquired: datetime
    animal: Animal  # Note: typed as base class


# Create instances with different subclasses
fido = Pet(acquired=datetime.now(), animal=Dog(name="Fido", breed="Corgi"))
whiskers = Pet(acquired=datetime.now(), animal=Cat(name="Whiskers", indoor=True, personality=Personality.GRUMPY))

# Serialize and deserialize - subclasses and enums preserved automatically!
whiskers_json = json.dumps(whiskers)
whiskers_restored = json.loads(whiskers_json)

assert isinstance(whiskers_restored.animal, Cat)  # ✓ Still a Cat, not just Animal
assert whiskers_restored.animal.personality == Personality.GRUMPY  # ✓ Enum preserved
assert whiskers_restored.animal.indoor is True  # ✓ All attributes intact
