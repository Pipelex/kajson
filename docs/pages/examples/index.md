# Examples

This section contains practical examples demonstrating how to use Kajson in real-world scenarios.

## Available Examples

### [REST API Integration](rest-api.md)

Learn how to use Kajson with REST APIs:
- Serializing Pydantic models for API responses
- Deserializing API requests with validation
- Handling datetime fields in API payloads
- Error responses with proper status codes
- Building type-safe API clients

### [Configuration Files](config-files.md)

Manage application configuration with Kajson:
- Loading and saving configuration files
- Type-safe configuration models
- Environment-specific configurations
- Configuration validation and defaults
- Hot-reloading configuration changes

### [Data Persistence](data-persistence.md)

Use Kajson for data storage and retrieval:
- Saving complex objects to JSON files
- Database serialization patterns
- Caching with Redis/Memcached
- Data migration strategies
- Backup and restore operations

## Quick Examples

### API Response Serialization

```python
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
import kajson

class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None

class ApiResponse(BaseModel):
    status: str
    timestamp: datetime
    data: Optional[User] = None
    errors: List[str] = []

# Create response
user = User(
    id=123,
    username="alice",
    email="alice@example.com",
    created_at=datetime.now()
)

response = ApiResponse(
    status="success",
    timestamp=datetime.now(),
    data=user
)

# Serialize for API
json_response = kajson.dumps(response, indent=2)
print(json_response)
```

### Configuration Management

```python
from pydantic import BaseModel, Field
from typing import Dict, Any
import kajson

class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    username: str
    password: str
    pool_size: int = Field(default=10, ge=1, le=100)

class AppConfig(BaseModel):
    debug: bool = False
    database: DatabaseConfig
    features: Dict[str, bool] = {}
    metadata: Dict[str, Any] = {}

# Load configuration
with open("config.json", "r") as f:
    config = kajson.load(f)

# Type-safe access
if config.debug:
    print(f"Connecting to {config.database.host}:{config.database.port}")
```

### Data Persistence

```python
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Dict
import kajson

class Task(BaseModel):
    id: str
    title: str
    description: str
    due_date: datetime
    completed: bool = False
    tags: List[str] = []
    time_spent: timedelta = timedelta()

class Project(BaseModel):
    name: str
    created_at: datetime
    tasks: Dict[str, Task] = {}

# Save project data
project = Project(
    name="Website Redesign",
    created_at=datetime.now()
)

# Add tasks
project.tasks["task-1"] = Task(
    id="task-1",
    title="Design mockups",
    description="Create initial design mockups",
    due_date=datetime.now() + timedelta(days=7),
    tags=["design", "ui"]
)

# Persist to file
with open("project.json", "w") as f:
    kajson.dump(project, f, indent=2)

# Load and resume work
with open("project.json", "r") as f:
    loaded_project = kajson.load(f)
    
# All types preserved
assert isinstance(loaded_project, Project)
assert isinstance(loaded_project.tasks["task-1"].due_date, datetime)
```

## Common Patterns

### Error Handling Pattern

```python
import kajson
from typing import Any, Optional

def safe_load_json(file_path: str) -> Optional[Any]:
    """Safely load JSON with comprehensive error handling"""
    try:
        with open(file_path, "r") as f:
            return kajson.load(f)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except kajson.JSONDecodeError as e:
        print(f"Invalid JSON in {file_path}: {e}")
    except kajson.KajsonDecoderError as e:
        print(f"Type reconstruction failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None
```

### Streaming Large Data

```python
import kajson
from typing import Iterator, Any

def stream_json_objects(file_path: str) -> Iterator[Any]:
    """Stream objects from a JSON array file"""
    with open(file_path, "r") as f:
        # Skip opening bracket
        f.read(1)  # [
        
        buffer = ""
        depth = 0
        in_string = False
        escape = False
        
        while True:
            char = f.read(1)
            if not char:
                break
                
            buffer += char
            
            # Track JSON structure
            if not escape:
                if char == '"' and not in_string:
                    in_string = True
                elif char == '"' and in_string:
                    in_string = False
                elif char == '{' and not in_string:
                    depth += 1
                elif char == '}' and not in_string:
                    depth -= 1
                    
                    if depth == 0:
                        # Complete object
                        yield kajson.loads(buffer.strip().rstrip(','))
                        buffer = ""
                elif char == '\\':
                    escape = True
            else:
                escape = False
```

## Best Practices

1. **Always use type hints** for better IDE support and documentation
2. **Handle errors gracefully** when dealing with external data
3. **Validate data** using Pydantic models before processing
4. **Use appropriate formatting** (indent for human-readable, compact for transmission)
5. **Test serialization round-trips** to ensure data integrity

## Next Steps

Explore the specific examples:
- [REST API Integration](rest-api.md) - Build robust APIs
- [Configuration Files](config-files.md) - Manage app configuration
- [Data Persistence](data-persistence.md) - Store and retrieve data
