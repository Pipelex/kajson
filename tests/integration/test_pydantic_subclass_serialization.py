# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for Pydantic subclass serialization and deserialization.

These tests demonstrate Kajson's ability to handle polymorphism where:
- A field is declared with a base class type
- The actual instance is a subclass of that base class
- Deserialization correctly reconstructs the subclass instance
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field
from typing_extensions import override

from kajson import kajson
from kajson.kajson_manager import KajsonManager


class TestPydanticSubclassSerialization:
    """Tests demonstrating subclass serialization and deserialization with Pydantic models."""

    def test_basic_subclass_serialization(self):
        """Test basic subclass serialization where field type is base class but instance is subclass."""

        # Define base class
        class Animal(BaseModel):
            name: str
            species: str

            def make_sound(self) -> str:
                return "Some generic animal sound"

        # Define subclasses
        class Dog(Animal):
            breed: str
            is_good_boy: bool = True

            @override
            def make_sound(self) -> str:
                return "Woof!"

        class Cat(Animal):
            lives_remaining: int = 9
            is_indoor: bool = True

            @override
            def make_sound(self) -> str:
                return "Meow!"

        # Define container class with base class field type
        class Pet(BaseModel):
            owner: str
            animal: Animal  # Field declared as base class
            registration_date: str

        # Set fake module names to force class registry usage
        Animal.__module__ = "test.fake.module"
        Dog.__module__ = "test.fake.module"
        Cat.__module__ = "test.fake.module"
        Pet.__module__ = "test.fake.module"

        # Create instances with subclass objects
        dog_pet = Pet(owner="Alice", animal=Dog(name="Buddy", species="Canis lupus", breed="Golden Retriever"), registration_date="2024-01-15")

        cat_pet = Pet(
            owner="Bob", animal=Cat(name="Whiskers", species="Felis catus", lives_remaining=8, is_indoor=True), registration_date="2024-02-20"
        )

        print(f"Original dog pet: {dog_pet}")
        print(f"Dog animal type: {type(dog_pet.animal)}")
        print(f"Dog sound: {dog_pet.animal.make_sound()}")

        print(f"\nOriginal cat pet: {cat_pet}")
        print(f"Cat animal type: {type(cat_pet.animal)}")
        print(f"Cat sound: {cat_pet.animal.make_sound()}")

        # Serialize both pets
        dog_json = kajson.dumps(dog_pet)
        cat_json = kajson.dumps(cat_pet)

        print(f"\nSerialized dog pet JSON: {dog_json}")
        print(f"Serialized cat pet JSON: {cat_json}")

        # Register classes in the class registry for deserialization
        # (In real scenarios, these would be available at module level or registered dynamically)
        registry = KajsonManager.get_class_registry()
        registry.register_class(Animal)
        registry.register_class(Dog)
        registry.register_class(Cat)
        registry.register_class(Pet)

        try:
            # Deserialize and verify subclass types are preserved
            restored_dog_pet = kajson.loads(dog_json)
            restored_cat_pet = kajson.loads(cat_json)

            print(f"\nRestored dog pet: {restored_dog_pet}")
            print(f"Restored dog animal type: {type(restored_dog_pet.animal)}")
            print(f"Restored dog sound: {restored_dog_pet.animal.make_sound()}")

            print(f"\nRestored cat pet: {restored_cat_pet}")
            print(f"Restored cat animal type: {type(restored_cat_pet.animal)}")
            print(f"Restored cat sound: {restored_cat_pet.animal.make_sound()}")

            # Verify subclass-specific attributes are preserved
            assert isinstance(restored_dog_pet.animal, Dog)
            assert restored_dog_pet.animal.breed == "Golden Retriever"
            assert restored_dog_pet.animal.is_good_boy is True
            assert restored_dog_pet.animal.make_sound() == "Woof!"

            assert isinstance(restored_cat_pet.animal, Cat)
            assert restored_cat_pet.animal.lives_remaining == 8
            assert restored_cat_pet.animal.is_indoor is True
            assert restored_cat_pet.animal.make_sound() == "Meow!"

            # Verify base class attributes are also preserved
            assert restored_dog_pet.animal.name == "Buddy"
            assert restored_dog_pet.animal.species == "Canis lupus"
            assert restored_cat_pet.animal.name == "Whiskers"
            assert restored_cat_pet.animal.species == "Felis catus"

            print("✅ Subclass serialization and deserialization successful!")
        finally:
            # Clean up registry
            registry.teardown()

    def test_multiple_inheritance_levels(self):
        """Test multiple levels of inheritance: Vehicle -> MotorVehicle -> Car -> SportsCar."""

        # Define vehicle hierarchy with multiple inheritance levels
        class Vehicle(BaseModel):
            make: str
            model: str
            year: int

            def get_info(self) -> str:
                return f"{self.year} {self.make} {self.model}"

        class MotorVehicle(Vehicle):
            engine_type: str
            fuel_capacity: float

        class Car(MotorVehicle):
            doors: int
            is_convertible: bool = False

            @override
            def get_info(self) -> str:
                return f"{super().get_info()} - {self.doors} door car"

        class SportsCar(Car):
            top_speed_mph: int
            acceleration_0_60: float

            @override
            def get_info(self) -> str:
                return f"{super().get_info()} - Sports car (0-60: {self.acceleration_0_60}s)"

        # Set fake module names to force class registry usage
        Vehicle.__module__ = "test.fake.module"
        MotorVehicle.__module__ = "test.fake.module"
        Car.__module__ = "test.fake.module"
        SportsCar.__module__ = "test.fake.module"

        # Create a sports car instance (4 levels deep in inheritance)
        sports_car = SportsCar(
            make="Ferrari",
            model="488 GTB",
            year=2023,
            engine_type="V8 Twin-Turbo",
            fuel_capacity=78.0,
            doors=2,
            is_convertible=False,
            top_speed_mph=205,
            acceleration_0_60=3.0,
        )

        print(f"Original sports car: {sports_car.get_info()}")

        # Serialize
        json_str = kajson.dumps(sports_car)
        print(f"Serialized sports car JSON length: {len(json_str)} characters")

        # Register classes for deserialization
        registry = KajsonManager.get_class_registry()
        registry.register_class(Vehicle)
        registry.register_class(MotorVehicle)
        registry.register_class(Car)
        registry.register_class(SportsCar)

        try:
            # Deserialize and verify all inheritance levels are preserved
            restored_sports_car = kajson.loads(json_str)

            print(f"Restored sports car: {restored_sports_car.get_info()}")

            # Verify it's the correct subclass type
            assert isinstance(restored_sports_car, SportsCar)
            assert isinstance(restored_sports_car, Car)  # Also a Car
            assert isinstance(restored_sports_car, MotorVehicle)  # Also a MotorVehicle
            assert isinstance(restored_sports_car, Vehicle)  # Also a Vehicle

            # Verify SportsCar-specific attributes
            assert restored_sports_car.top_speed_mph == 205
            assert restored_sports_car.acceleration_0_60 == 3.0

            # Verify Car-level attributes
            assert restored_sports_car.doors == 2
            assert restored_sports_car.is_convertible is False

            # Verify MotorVehicle-level attributes
            assert restored_sports_car.engine_type == "V8 Twin-Turbo"
            assert restored_sports_car.fuel_capacity == 78.0

            # Verify Vehicle-level attributes
            assert restored_sports_car.make == "Ferrari"
            assert restored_sports_car.model == "488 GTB"
            assert restored_sports_car.year == 2023

            print("✅ Multiple inheritance levels preserved correctly!")
        finally:
            registry.teardown()

    def test_fleet_with_mixed_vehicle_types(self):
        """Test fleet management with mixed vehicle subclass types."""

        # Define vehicle hierarchy
        class Vehicle(BaseModel):
            make: str
            model: str
            year: int

            def get_info(self) -> str:
                return f"{self.year} {self.make} {self.model}"

        class MotorVehicle(Vehicle):
            engine_type: str
            fuel_capacity: float

        class Car(MotorVehicle):
            doors: int
            is_convertible: bool = False

            @override
            def get_info(self) -> str:
                return f"{super().get_info()} - {self.doors} door car"

        class SportsCar(Car):
            top_speed_mph: int
            acceleration_0_60: float

            @override
            def get_info(self) -> str:
                return f"{super().get_info()} - Sports car (0-60: {self.acceleration_0_60}s)"

        class Truck(MotorVehicle):
            bed_length_ft: float
            towing_capacity_lbs: int

            @override
            def get_info(self) -> str:
                return f"{super().get_info()} - Truck (towing: {self.towing_capacity_lbs} lbs)"

        class Fleet(BaseModel):
            company: str
            vehicles: List[Vehicle]  # List of base class, but can contain subclasses
            manager: str

        # Set fake module names to force class registry usage
        Vehicle.__module__ = "test.fake.module"
        MotorVehicle.__module__ = "test.fake.module"
        Car.__module__ = "test.fake.module"
        SportsCar.__module__ = "test.fake.module"
        Truck.__module__ = "test.fake.module"
        Fleet.__module__ = "test.fake.module"

        # Create fleet with mixed vehicle types
        fleet = Fleet(
            company="City Transport Co",
            manager="John Smith",
            vehicles=[
                SportsCar(
                    make="Ferrari",
                    model="488 GTB",
                    year=2023,
                    engine_type="V8 Twin-Turbo",
                    fuel_capacity=78.0,
                    doors=2,
                    is_convertible=False,
                    top_speed_mph=205,
                    acceleration_0_60=3.0,
                ),
                Truck(
                    make="Ford", model="F-150", year=2024, engine_type="V6 EcoBoost", fuel_capacity=98.0, bed_length_ft=6.5, towing_capacity_lbs=13200
                ),
                Car(make="Honda", model="Civic", year=2024, engine_type="4-Cylinder", fuel_capacity=47.0, doors=4, is_convertible=False),
            ],
        )

        print(f"Original fleet: {fleet.company}")
        for i, vehicle in enumerate(fleet.vehicles):
            print(f"  Vehicle {i + 1}: {type(vehicle).__name__} - {vehicle.get_info()}")

        # Serialize the fleet
        fleet_json = kajson.dumps(fleet)
        print(f"\nSerialized fleet JSON length: {len(fleet_json)} characters")

        # Register classes in the class registry for deserialization
        registry = KajsonManager.get_class_registry()
        registry.register_class(Vehicle)
        registry.register_class(MotorVehicle)
        registry.register_class(Car)
        registry.register_class(SportsCar)
        registry.register_class(Truck)
        registry.register_class(Fleet)

        try:
            # Deserialize and verify all subclass types are preserved
            restored_fleet = kajson.loads(fleet_json)

            print(f"\nRestored fleet: {restored_fleet.company}")
            for i, vehicle in enumerate(restored_fleet.vehicles):
                print(f"  Vehicle {i + 1}: {type(vehicle).__name__} - {vehicle.get_info()}")

            # Verify fleet-level data
            assert restored_fleet.company == "City Transport Co"
            assert restored_fleet.manager == "John Smith"
            assert len(restored_fleet.vehicles) == 3

            print("✅ Fleet with mixed vehicle types preserved correctly!")
        finally:
            registry.teardown()

    def test_subclass_specific_attribute_preservation(self):
        """Test that subclass-specific attributes are preserved during serialization."""

        # Define vehicle hierarchy
        class Vehicle(BaseModel):
            make: str
            model: str
            year: int

        class MotorVehicle(Vehicle):
            engine_type: str
            fuel_capacity: float

        class Car(MotorVehicle):
            doors: int
            is_convertible: bool = False

        class SportsCar(Car):
            top_speed_mph: int
            acceleration_0_60: float

        class Truck(MotorVehicle):
            bed_length_ft: float
            towing_capacity_lbs: int

        class Fleet(BaseModel):
            company: str
            vehicles: List[Vehicle]

        # Set fake module names
        Vehicle.__module__ = "test.fake.module"
        MotorVehicle.__module__ = "test.fake.module"
        Car.__module__ = "test.fake.module"
        SportsCar.__module__ = "test.fake.module"
        Truck.__module__ = "test.fake.module"
        Fleet.__module__ = "test.fake.module"

        # Create fleet
        fleet = Fleet(
            company="Test Fleet",
            vehicles=[
                SportsCar(
                    make="Ferrari",
                    model="488 GTB",
                    year=2023,
                    engine_type="V8 Twin-Turbo",
                    fuel_capacity=78.0,
                    doors=2,
                    is_convertible=False,
                    top_speed_mph=205,
                    acceleration_0_60=3.0,
                ),
                Truck(
                    make="Ford", model="F-150", year=2024, engine_type="V6 EcoBoost", fuel_capacity=98.0, bed_length_ft=6.5, towing_capacity_lbs=13200
                ),
                Car(make="Honda", model="Civic", year=2024, engine_type="4-Cylinder", fuel_capacity=47.0, doors=4, is_convertible=False),
            ],
        )

        fleet_json = kajson.dumps(fleet)

        registry = KajsonManager.get_class_registry()
        registry.register_class(Vehicle)
        registry.register_class(MotorVehicle)
        registry.register_class(Car)
        registry.register_class(SportsCar)
        registry.register_class(Truck)
        registry.register_class(Fleet)

        try:
            restored_fleet = kajson.loads(fleet_json)

            # First vehicle should be SportsCar with all specific attributes
            sports_car = restored_fleet.vehicles[0]
            assert isinstance(sports_car, SportsCar)
            assert sports_car.make == "Ferrari"
            assert sports_car.top_speed_mph == 205
            assert sports_car.acceleration_0_60 == 3.0
            assert sports_car.doors == 2

            # Second vehicle should be Truck with all specific attributes
            truck = restored_fleet.vehicles[1]
            assert isinstance(truck, Truck)
            assert truck.make == "Ford"
            assert truck.bed_length_ft == 6.5
            assert truck.towing_capacity_lbs == 13200

            # Third vehicle should be Car (not SportsCar) with specific attributes
            car = restored_fleet.vehicles[2]
            assert isinstance(car, Car)
            assert not isinstance(car, SportsCar)  # Make sure it's not the subclass
            assert car.make == "Honda"
            assert car.doors == 4

            print("✅ Subclass-specific attributes preserved correctly!")
        finally:
            registry.teardown()

    def test_abstract_base_with_concrete_subclasses(self):
        """Test serialization with abstract base classes and concrete implementations."""

        from abc import ABC, abstractmethod

        # Define abstract base class
        class Shape(BaseModel, ABC):
            name: str
            color: str

            @abstractmethod
            def area(self) -> float:
                pass

            @abstractmethod
            def perimeter(self) -> float:
                pass

        # Define concrete subclasses
        class Rectangle(Shape):
            width: float = Field(gt=0)
            height: float = Field(gt=0)

            @override
            def area(self) -> float:
                return self.width * self.height

            @override
            def perimeter(self) -> float:
                return 2 * (self.width + self.height)

        class Circle(Shape):
            radius: float = Field(gt=0)

            @override
            def area(self) -> float:
                import math

                return math.pi * self.radius**2

            @override
            def perimeter(self) -> float:
                import math

                return 2 * math.pi * self.radius

        # Define container with abstract base type
        class Drawing(BaseModel):
            title: str
            shapes: List[Shape]  # Abstract base class type
            artist: str

        # Set fake module names to force class registry usage
        Shape.__module__ = "test.fake.module"
        Rectangle.__module__ = "test.fake.module"
        Circle.__module__ = "test.fake.module"
        Drawing.__module__ = "test.fake.module"

        # Create drawing with concrete shape instances
        drawing = Drawing(
            title="Geometric Art",
            artist="Jane Doe",
            shapes=[
                Rectangle(name="Main Rectangle", color="blue", width=10.0, height=5.0),
                Circle(name="Center Circle", color="red", radius=3.0),
                Rectangle(name="Small Square", color="green", width=2.0, height=2.0),
            ],
        )

        print(f"Original drawing: {drawing.title}")
        for shape in drawing.shapes:
            print(f"  {type(shape).__name__}: {shape.name} ({shape.color}) - Area: {shape.area():.2f}")

        # Serialize the drawing
        drawing_json = kajson.dumps(drawing)
        print(f"\nSerialized drawing JSON length: {len(drawing_json)} characters")

        # Register classes in the class registry for deserialization
        registry = KajsonManager.get_class_registry()
        registry.register_class(Shape)
        registry.register_class(Rectangle)
        registry.register_class(Circle)
        registry.register_class(Drawing)

        try:
            # Deserialize and verify concrete types are preserved
            restored_drawing = kajson.loads(drawing_json)

            print(f"\nRestored drawing: {restored_drawing.title}")
            for shape in restored_drawing.shapes:
                print(f"  {type(shape).__name__}: {shape.name} ({shape.color}) - Area: {shape.area():.2f}")

            # Verify concrete subclass types and functionality
            assert len(restored_drawing.shapes) == 3

            # First shape should be Rectangle
            rect1 = restored_drawing.shapes[0]
            assert isinstance(rect1, Rectangle)
            assert rect1.name == "Main Rectangle"
            assert rect1.width == 10.0
            assert rect1.height == 5.0
            assert rect1.area() == 50.0

            # Second shape should be Circle
            circle = restored_drawing.shapes[1]
            assert isinstance(circle, Circle)
            assert circle.name == "Center Circle"
            assert circle.radius == 3.0
            assert abs(circle.area() - 28.27) < 0.01  # π * 3² ≈ 28.27

            # Third shape should be Rectangle (square)
            rect2 = restored_drawing.shapes[2]
            assert isinstance(rect2, Rectangle)
            assert rect2.name == "Small Square"
            assert rect2.width == 2.0
            assert rect2.height == 2.0
            assert rect2.area() == 4.0

            print("✅ Abstract base class with concrete subclasses preserved correctly!")
        finally:
            # Clean up registry
            registry.teardown()
