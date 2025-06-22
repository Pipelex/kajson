# Pydantic Integration

Kajson provides seamless integration with Pydantic v2 models, automatically handling serialization and deserialization while preserving validation and type safety.

## Basic Pydantic Model Serialization

### Simple Models

```python
from pydantic import BaseModel
import kajson

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True

# Create instance
user = User(id=1, name="Alice", email="alice@example.com")

# Serialize to JSON
json_str = kajson.dumps(user, indent=2)
print(json_str)

# Deserialize back to User instance
restored_user = kajson.loads(json_str)
assert isinstance(restored_user, User)
assert user == restored_user
```

### Models with DateTime Fields

```python
from datetime import datetime
from pydantic import BaseModel
import kajson

class Event(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: str | None = None

# Create event
event = Event(
    title="Team Meeting",
    start_time=datetime(2025, 1, 15, 10, 0),
    end_time=datetime(2025, 1, 15, 11, 30)
)

# Serialize and deserialize
json_str = kajson.dumps(event)
restored = kajson.loads(json_str)

# DateTime objects are preserved
assert isinstance(restored.start_time, datetime)
```

## Nested Models

### One-to-Many Relationships

```python
from typing import List
from datetime import datetime
from pydantic import BaseModel
import kajson

class Comment(BaseModel):
    id: int
    author: str
    content: str
    created_at: datetime

class BlogPost(BaseModel):
    id: int
    title: str
    content: str
    author: str
    created_at: datetime
    comments: List[Comment]

# Create nested structure
post = BlogPost(
    id=1,
    title="Understanding Kajson",
    content="Kajson makes working with Pydantic models easy...",
    author="Alice",
    created_at=datetime.now(),
    comments=[
        Comment(id=1, author="Bob", content="Great post!", created_at=datetime.now()),
        Comment(id=2, author="Carol", content="Very helpful", created_at=datetime.now())
    ]
)

# Serialize and deserialize
json_str = kajson.dumps(post)
restored = kajson.loads(json_str)

# All nested models are properly restored
assert isinstance(restored, BlogPost)
assert all(isinstance(comment, Comment) for comment in restored.comments)
```

### Complex Nested Structures

```python
from typing import List, Dict, Optional
from pydantic import BaseModel
import kajson

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class Company(BaseModel):
    name: str
    address: Address
    
class Person(BaseModel):
    name: str
    age: int
    addresses: Dict[str, Address]
    employer: Optional[Company] = None

# Create complex nested structure
person = Person(
    name="Alice",
    age=30,
    addresses={
        "home": Address(
            street="123 Main St",
            city="New York",
            country="USA",
            postal_code="10001"
        ),
        "work": Address(
            street="456 Business Ave",
            city="New York",
            country="USA",
            postal_code="10002"
        )
    },
    employer=Company(
        name="Tech Corp",
        address=Address(
            street="789 Tech Blvd",
            city="San Francisco",
            country="USA",
            postal_code="94105"
        )
    )
)

# Perfect serialization and deserialization
json_str = kajson.dumps(person)
restored = kajson.loads(json_str)
```

## Pydantic Validation

### Validation During Deserialization

```python
from pydantic import BaseModel, Field, validator
import kajson

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price must be positive")
    quantity: int = Field(ge=0, default=0)
    
    @validator('name')
    def name_must_be_capitalized(cls, v):
        if not v[0].isupper():
            raise ValueError('Product name must start with capital letter')
        return v

# Valid product
valid_json = '{"name": "Laptop", "price": 999.99, "quantity": 10, "__class__": "Product", "__module__": "__main__"}'
product = kajson.loads(valid_json)
print(f"Valid product: {product.name}")

# Invalid product - will raise validation error
try:
    invalid_json = '{"name": "laptop", "price": -100, "__class__": "Product", "__module__": "__main__"}'
    kajson.loads(invalid_json)
except kajson.KajsonDecoderError as e:
    print(f"Validation error: {e}")
```

### Custom Validators

```python
from pydantic import BaseModel, field_validator
from datetime import date
import kajson

class Person(BaseModel):
    name: str
    birth_date: date
    
    @field_validator('birth_date')
    def validate_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Person must be at least 18 years old')
        return v

# Create and serialize
person = Person(name="Alice", birth_date=date(1990, 1, 1))
json_str = kajson.dumps(person)

# Validation happens on deserialization
restored = kajson.loads(json_str)
```

## Advanced Pydantic Features

### Model Config

```python
from pydantic import BaseModel, ConfigDict
import kajson

class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_to_lower=True,
        validate_assignment=True
    )
    
    username: str
    email: str

# Pydantic config is respected
user = User(username="  ALICE  ", email="  ALICE@EXAMPLE.COM  ")
print(user.username)  # "alice"
print(user.email)     # "alice@example.com"

# Serialize and deserialize
json_str = kajson.dumps(user)
restored = kajson.loads(json_str)
```

### Union Types and Discriminated Unions

```python
from typing import Union, Literal
from pydantic import BaseModel, Field
import kajson

class Cat(BaseModel):
    pet_type: Literal["cat"]
    meows: int

class Dog(BaseModel):
    pet_type: Literal["dog"] 
    barks: int

class Bird(BaseModel):
    pet_type: Literal["bird"]
    chirps: int

Pet = Union[Cat, Dog, Bird]

class Person(BaseModel):
    name: str
    pet: Pet = Field(discriminator='pet_type')

# Create person with different pets
people = [
    Person(name="Alice", pet=Cat(pet_type="cat", meows=10)),
    Person(name="Bob", pet=Dog(pet_type="dog", barks=5)),
    Person(name="Carol", pet=Bird(pet_type="bird", chirps=20))
]

# Serialize list
json_str = kajson.dumps(people)

# Deserialize - correct types are restored
restored = kajson.loads(json_str)
assert isinstance(restored[0].pet, Cat)
assert isinstance(restored[1].pet, Dog)
assert isinstance(restored[2].pet, Bird)
```

### Generic Models

```python
from typing import TypeVar, Generic, List
from pydantic import BaseModel
import kajson

T = TypeVar('T')

class PagedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int

class User(BaseModel):
    id: int
    name: str

# Create paged response
users = [User(id=i, name=f"User{i}") for i in range(1, 6)]
response = PagedResponse[User](
    items=users,
    page=1,
    page_size=5,
    total=100
)

# Serialize and deserialize
json_str = kajson.dumps(response)
restored = kajson.loads(json_str)

# Generic type information is preserved
assert all(isinstance(user, User) for user in restored.items)
```

## Working with Lists and Dicts of Models

```python
from typing import List, Dict
from pydantic import BaseModel
import kajson

class Task(BaseModel):
    id: int
    title: str
    completed: bool = False

# List of models
tasks = [
    Task(id=1, title="Write documentation"),
    Task(id=2, title="Review PR", completed=True),
    Task(id=3, title="Deploy to production")
]

# Dict of models
task_dict = {
    "urgent": Task(id=4, title="Fix critical bug"),
    "normal": Task(id=5, title="Add new feature"),
    "low": Task(id=6, title="Update dependencies")
}

# Both serialize perfectly
tasks_json = kajson.dumps(tasks)
dict_json = kajson.dumps(task_dict)

# And deserialize with correct types
restored_tasks = kajson.loads(tasks_json)
restored_dict = kajson.loads(dict_json)

assert all(isinstance(task, Task) for task in restored_tasks)
assert all(isinstance(task, Task) for task in restored_dict.values())
```

## Best Practices

### 1. Use Type Annotations

Always use proper type annotations for better IDE support and validation:

```python
from typing import Optional, List
from pydantic import BaseModel

class User(BaseModel):
    name: str  # Required
    email: Optional[str] = None  # Optional with None default
    tags: List[str] = []  # List with empty default
```

### 2. Handle Validation Errors

Always handle potential validation errors when deserializing untrusted data:

```python
try:
    user = kajson.loads(untrusted_json)
except kajson.KajsonDecoderError as e:
    # Log error, return error response, etc.
    print(f"Invalid data: {e}")
```

### 3. Use Field Descriptions

Document your models for better API documentation:

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(description="Product name", example="Laptop")
    price: float = Field(description="Price in USD", gt=0, example=999.99)
    in_stock: bool = Field(description="Whether product is available", default=True)
```

### 4. Separate DTOs from Domain Models

Consider using separate Pydantic models for data transfer:

```python
# Domain model
class User:
    def __init__(self, id: int, name: str, password_hash: str):
        self.id = id
        self.name = name
        self._password_hash = password_hash

# DTO for serialization
class UserDTO(BaseModel):
    id: int
    name: str
    # Note: no password field

    @classmethod
    def from_domain(cls, user: User) -> "UserDTO":
        return cls(id=user.id, name=user.name)
```

## Next Steps

- Learn about [Custom Types](custom-types.md) to extend Kajson further
- Explore [Error Handling](error-handling.md) for robust applications
- Check out [Examples](../examples/index.md) for real-world use cases 