# REST API Integration

This example demonstrates how to use Kajson with REST APIs for building type-safe, robust API endpoints and clients.

## FastAPI Integration

### Basic API with Pydantic Models

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
import kajson

app = FastAPI()

# Models
class User(BaseModel):
    id: int
    username: str = Field(min_length=3, max_length=20)
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    user: User
    token: str

# In-memory storage for example
users_db = {}
next_id = 1

@app.post("/users", response_model=UserResponse)
async def create_user(request: CreateUserRequest):
    global next_id
    
    # Check if username exists
    if any(u.username == request.username for u in users_db.values()):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    user = User(
        id=next_id,
        username=request.username,
        email=request.email,
        created_at=datetime.now()
    )
    
    users_db[next_id] = user
    next_id += 1
    
    # Generate token (simplified for example)
    token = f"token_{user.id}_{user.username}"
    
    return UserResponse(user=user, token=token)

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return users_db[user_id]

# Custom JSON response using Kajson
@app.get("/users/{user_id}/export")
async def export_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    # Use Kajson for custom serialization
    return kajson.dumps({
        "exported_at": datetime.now(),
        "format_version": "1.0",
        "data": user
    }, indent=2)
```

### API Error Handling

```python
from enum import Enum
from typing import Any, Dict

class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class ApiError(BaseModel):
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None

@app.exception_handler(kajson.KajsonDecoderError)
async def kajson_error_handler(request, exc):
    error = ApiError(
        code=ErrorCode.VALIDATION_ERROR,
        message="Invalid data format",
        details={"error": str(exc)},
        request_id=request.headers.get("X-Request-ID")
    )
    
    return JSONResponse(
        status_code=400,
        content=kajson.loads(kajson.dumps(error))
    )

@app.post("/data/import")
async def import_data(request: Request):
    try:
        # Get raw body
        body = await request.body()
        
        # Use Kajson to deserialize with type preservation
        data = kajson.loads(body)
        
        # Process based on type
        if isinstance(data, User):
            # Handle user import
            return {"message": "User imported", "id": data.id}
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported data type"
            )
            
    except kajson.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON: {str(e)}"
        )
```

## Building a Type-Safe API Client

```python
import httpx
import kajson
from typing import TypeVar, Type, Optional, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class ApiClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=timeout)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def set_auth_token(self, token: str):
        """Set authentication token"""
        self.headers["Authorization"] = f"Bearer {token}"
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Any] = None,
        params: Optional[dict] = None
    ) -> httpx.Response:
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        
        kwargs = {
            "headers": self.headers,
            "params": params
        }
        
        if data is not None:
            kwargs["content"] = kajson.dumps(data)
        
        response = self.client.request(method, url, **kwargs)
        response.raise_for_status()
        
        return response
    
    def get(
        self,
        endpoint: str,
        response_type: Type[T],
        params: Optional[dict] = None
    ) -> T:
        """GET request with type-safe response"""
        response = self._request("GET", endpoint, params=params)
        return kajson.loads(response.text, cls=response_type)
    
    def post(
        self,
        endpoint: str,
        data: BaseModel,
        response_type: Type[T]
    ) -> T:
        """POST request with type-safe request and response"""
        response = self._request("POST", endpoint, data=data)
        return kajson.loads(response.text, cls=response_type)
    
    def close(self):
        """Close the client"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()

# Usage example
class TodoItem(BaseModel):
    id: int
    title: str
    completed: bool
    created_at: datetime

class CreateTodoRequest(BaseModel):
    title: str
    description: Optional[str] = None

async def example_usage():
    with ApiClient("https://api.example.com") as client:
        # Create a todo
        create_request = CreateTodoRequest(
            title="Complete documentation",
            description="Finish writing Kajson examples"
        )
        
        todo = client.post(
            "/todos",
            data=create_request,
            response_type=TodoItem
        )
        
        print(f"Created todo #{todo.id}: {todo.title}")
        
        # Get all todos
        todos = client.get(
            "/todos",
            response_type=List[TodoItem]
        )
        
        for todo in todos:
            print(f"- [{todo.completed}] {todo.title}")
```

## Pagination Support

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total_pages: int
    total_items: int
    has_next: bool
    has_prev: bool
    
    @property
    def next_page(self) -> Optional[int]:
        return self.page + 1 if self.has_next else None
    
    @property
    def prev_page(self) -> Optional[int]:
        return self.page - 1 if self.has_prev else None

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

@app.get("/users", response_model=PaginatedResponse[User])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None
):
    # Filter users
    filtered_users = list(users_db.values())
    if search:
        filtered_users = [
            u for u in filtered_users
            if search.lower() in u.username.lower()
        ]
    
    # Calculate pagination
    total_items = len(filtered_users)
    total_pages = (total_items + page_size - 1) // page_size
    
    # Get page items
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered_users[start:end]
    
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        total_items=total_items,
        has_next=page < total_pages,
        has_prev=page > 1
    )
```

## Webhook Processing

```python
from typing import Any, Dict
import hmac
import hashlib

class WebhookEvent(BaseModel):
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None

class WebhookProcessor:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.handlers = {}
    
    def register_handler(self, event_type: str):
        """Decorator to register event handlers"""
        def decorator(func):
            self.handlers[event_type] = func
            return func
        return decorator
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        expected = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    async def process(self, request: Request) -> Dict[str, Any]:
        """Process incoming webhook"""
        # Get raw body
        body = await request.body()
        
        # Verify signature
        signature = request.headers.get("X-Webhook-Signature")
        if signature and not self.verify_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse event
        event = kajson.loads(body, cls=WebhookEvent)
        
        # Find handler
        handler = self.handlers.get(event.event_type)
        if not handler:
            raise HTTPException(
                status_code=400,
                detail=f"No handler for event type: {event.event_type}"
            )
        
        # Process event
        result = await handler(event)
        
        return {
            "status": "processed",
            "event_type": event.event_type,
            "timestamp": datetime.now(),
            "result": result
        }

# Usage
webhook_processor = WebhookProcessor(secret_key="your-secret-key")

@webhook_processor.register_handler("user.created")
async def handle_user_created(event: WebhookEvent):
    user_data = event.data
    print(f"New user created: {user_data.get('username')}")
    # Process the event...
    return {"processed": True}

@app.post("/webhooks")
async def receive_webhook(request: Request):
    return await webhook_processor.process(request)
```

## Rate Limiting with Metadata

```python
from datetime import datetime, timedelta
from typing import Dict
import asyncio

class RateLimitInfo(BaseModel):
    limit: int
    remaining: int
    reset_at: datetime
    window_seconds: int = 3600

class RateLimiter:
    def __init__(self, limit: int = 100, window_seconds: int = 3600):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}
        self._lock = asyncio.Lock()
    
    async def check_limit(self, key: str) -> RateLimitInfo:
        async with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)
            
            # Clean old requests
            if key in self.requests:
                self.requests[key] = [
                    dt for dt in self.requests[key]
                    if dt > window_start
                ]
            else:
                self.requests[key] = []
            
            # Check limit
            remaining = self.limit - len(self.requests[key])
            
            if remaining > 0:
                self.requests[key].append(now)
            
            reset_at = now + timedelta(seconds=self.window_seconds)
            
            return RateLimitInfo(
                limit=self.limit,
                remaining=max(0, remaining - 1),
                reset_at=reset_at,
                window_seconds=self.window_seconds
            )

# Middleware
rate_limiter = RateLimiter(limit=100)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Get client identifier
    client_id = request.client.host
    
    # Check rate limit
    limit_info = await rate_limiter.check_limit(client_id)
    
    if limit_info.remaining < 0:
        return JSONResponse(
            status_code=429,
            content=kajson.loads(kajson.dumps({
                "error": "Rate limit exceeded",
                "limit_info": limit_info
            }))
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(limit_info.limit)
    response.headers["X-RateLimit-Remaining"] = str(limit_info.remaining)
    response.headers["X-RateLimit-Reset"] = limit_info.reset_at.isoformat()
    
    return response
```

## Best Practices

1. **Always validate input** using Pydantic models
2. **Use proper status codes** for different error scenarios
3. **Include request IDs** for tracking and debugging
4. **Version your API** to handle breaking changes
5. **Document response formats** with response_model
6. **Handle datetime serialization** properly with Kajson
7. **Implement proper error responses** with consistent structure

## See Also

- [Configuration Files](config-files.md) - API configuration management
- [Error Handling Guide](../guide/error-handling.md) - Comprehensive error handling
- [Pydantic Integration](../guide/pydantic.md) - Advanced Pydantic usage
