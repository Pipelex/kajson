# Data Persistence

This example demonstrates how to use Kajson for data storage, retrieval, and management across various persistence backends.

## File-Based Storage

### JSON File Database

```python
from typing import Dict, List, Optional, TypeVar, Generic, Any
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import kajson
import fcntl
import os
from contextlib import contextmanager

T = TypeVar('T', bound=BaseModel)

class FileDatabase(Generic[T]):
    """Simple file-based JSON database with type safety"""
    
    def __init__(self, file_path: str, model_class: type[T]):
        self.file_path = Path(file_path)
        self.model_class = model_class
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure database file exists"""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_data({})
    
    @contextmanager
    def _file_lock(self, mode='r'):
        """File locking for concurrent access"""
        with open(self.file_path, mode) as f:
            # Acquire lock
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                yield f
            finally:
                # Release lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _read_data(self) -> Dict[str, Any]:
        """Read all data from file"""
        with self._file_lock('r') as f:
            content = f.read()
            if not content:
                return {}
            return kajson.loads(content)
    
    def _write_data(self, data: Dict[str, Any]):
        """Write all data to file"""
        with self._file_lock('w') as f:
            f.write(kajson.dumps(data, indent=2))
    
    def get(self, key: str) -> Optional[T]:
        """Get item by key"""
        data = self._read_data()
        if key in data:
            return self.model_class(**data[key])
        return None
    
    def get_all(self) -> List[T]:
        """Get all items"""
        data = self._read_data()
        return [self.model_class(**item) for item in data.values()]
    
    def set(self, key: str, item: T):
        """Set item by key"""
        data = self._read_data()
        data[key] = item.model_dump()
        self._write_data(data)
    
    def delete(self, key: str) -> bool:
        """Delete item by key"""
        data = self._read_data()
        if key in data:
            del data[key]
            self._write_data(data)
            return True
        return False
    
    def query(self, filter_func: callable) -> List[T]:
        """Query items with filter function"""
        return [item for item in self.get_all() if filter_func(item)]
    
    def update(self, key: str, update_func: callable) -> Optional[T]:
        """Update item by key"""
        data = self._read_data()
        if key in data:
            item = self.model_class(**data[key])
            updated_item = update_func(item)
            data[key] = updated_item.model_dump()
            self._write_data(data)
            return updated_item
        return None

# Usage example
class Task(BaseModel):
    id: str
    title: str
    description: str
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    tags: List[str] = []

# Create database
task_db = FileDatabase[Task]("data/tasks.json", Task)

# Add tasks
task1 = Task(
    id="task-001",
    title="Complete documentation",
    description="Write examples for Kajson",
    tags=["documentation", "priority"]
)
task_db.set(task1.id, task1)

# Query tasks
incomplete_tasks = task_db.query(lambda t: not t.completed)
priority_tasks = task_db.query(lambda t: "priority" in t.tags)

# Update task
task_db.update("task-001", lambda t: t.model_copy(update={"completed": True}))
```

### Versioned Data Storage

```python
from typing import List, Optional, Dict, Any
import shutil
from datetime import datetime
import hashlib

class VersionedStorage:
    """Storage with version history and rollback support"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.versions_path = self.base_path / "versions"
        self.versions_path.mkdir(exist_ok=True)
        self.current_file = self.base_path / "current.json"
        self.metadata_file = self.base_path / "metadata.json"
    
    def _get_file_hash(self, data: Any) -> str:
        """Get hash of data"""
        json_str = kajson.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def save(self, data: Any, message: str = "") -> str:
        """Save data with version"""
        # Create version info
        version_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        data_hash = self._get_file_hash(data)
        
        version_info = {
            "id": version_id,
            "timestamp": datetime.now(),
            "message": message,
            "hash": data_hash,
            "size": len(kajson.dumps(data))
        }
        
        # Save version file
        version_file = self.versions_path / f"{version_id}.json"
        with open(version_file, "w") as f:
            kajson.dump(data, f, indent=2)
        
        # Update current
        with open(self.current_file, "w") as f:
            kajson.dump(data, f, indent=2)
        
        # Update metadata
        metadata = self._load_metadata()
        metadata["versions"].append(version_info)
        metadata["current_version"] = version_id
        self._save_metadata(metadata)
        
        return version_id
    
    def load(self, version_id: Optional[str] = None) -> Any:
        """Load data (current or specific version)"""
        if version_id is None:
            if self.current_file.exists():
                with open(self.current_file, "r") as f:
                    return kajson.load(f)
            return None
        
        version_file = self.versions_path / f"{version_id}.json"
        if version_file.exists():
            with open(version_file, "r") as f:
                return kajson.load(f)
        
        raise ValueError(f"Version {version_id} not found")
    
    def list_versions(self) -> List[Dict[str, Any]]:
        """List all versions"""
        metadata = self._load_metadata()
        return metadata.get("versions", [])
    
    def rollback(self, version_id: str) -> Any:
        """Rollback to specific version"""
        data = self.load(version_id)
        
        # Save as new version
        new_version_id = self.save(
            data,
            f"Rollback to version {version_id}"
        )
        
        return data
    
    def diff(self, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two versions"""
        data1 = self.load(version1)
        data2 = self.load(version2)
        
        # Simple diff implementation
        return {
            "version1": version1,
            "version2": version2,
            "data1_keys": set(data1.keys()) if isinstance(data1, dict) else None,
            "data2_keys": set(data2.keys()) if isinstance(data2, dict) else None,
            "added": list(set(data2.keys()) - set(data1.keys())) if isinstance(data1, dict) and isinstance(data2, dict) else None,
            "removed": list(set(data1.keys()) - set(data2.keys())) if isinstance(data1, dict) and isinstance(data2, dict) else None
        }
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return kajson.load(f)
        return {"versions": [], "current_version": None}
    
    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata"""
        with open(self.metadata_file, "w") as f:
            kajson.dump(metadata, f, indent=2)

# Usage
storage = VersionedStorage("data/versioned")

# Save data
data_v1 = {"users": [{"id": 1, "name": "Alice"}]}
v1_id = storage.save(data_v1, "Initial version")

# Update and save new version
data_v2 = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
v2_id = storage.save(data_v2, "Added Bob")

# List versions
for version in storage.list_versions():
    print(f"{version['id']}: {version['message']}")

# Rollback if needed
storage.rollback(v1_id)
```

## Database Integration

### SQLite with JSON Fields

```python
import sqlite3
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

class SQLiteJSONStore:
    """SQLite storage with JSON field support"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    collection TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_collection 
                ON documents(collection)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON documents(created_at)
            """)
    
    @contextmanager
    def _get_conn(self):
        """Get database connection"""
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        
        # Enable JSON1 extension
        conn.execute("PRAGMA journal_mode=WAL")
        
        try:
            yield conn
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def insert(self, collection: str, doc_id: str, data: Any, metadata: Optional[Dict] = None):
        """Insert document"""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, collection, data, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (doc_id, collection, kajson.dumps(data), kajson.dumps(metadata))
            )
    
    def update(self, collection: str, doc_id: str, data: Any, metadata: Optional[Dict] = None):
        """Update document"""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE documents 
                SET data = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE collection = ? AND id = ?
                """,
                (kajson.dumps(data), kajson.dumps(metadata), collection, doc_id)
            )
    
    def get(self, collection: str, doc_id: str) -> Optional[Any]:
        """Get document by ID"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT data FROM documents WHERE collection = ? AND id = ?",
                (collection, doc_id)
            ).fetchone()
            
            if row:
                return kajson.loads(row["data"])
            return None
    
    def query(self, collection: str, json_path: str, value: Any) -> List[Dict[str, Any]]:
        """Query documents using JSON path"""
        with self._get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT id, data, created_at, updated_at
                FROM documents
                WHERE collection = ? 
                AND json_extract(data, ?) = ?
                """,
                (collection, json_path, kajson.dumps(value))
            ).fetchall()
            
            return [
                {
                    "id": row["id"],
                    "data": kajson.loads(row["data"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                for row in rows
            ]
    
    def delete(self, collection: str, doc_id: str) -> bool:
        """Delete document"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE collection = ? AND id = ?",
                (collection, doc_id)
            )
            return cursor.rowcount > 0
    
    def aggregate(self, collection: str, json_path: str, operation: str = "COUNT") -> Any:
        """Aggregate data using JSON path"""
        with self._get_conn() as conn:
            result = conn.execute(
                f"""
                SELECT {operation}(json_extract(data, ?)) as result
                FROM documents
                WHERE collection = ?
                """,
                (json_path, collection)
            ).fetchone()
            
            return result["result"] if result else None

# Usage
db = SQLiteJSONStore("data/store.db")

# Store user data
user = {
    "id": "user-123",
    "name": "Alice",
    "email": "alice@example.com",
    "preferences": {
        "theme": "dark",
        "notifications": True
    },
    "created_at": datetime.now()
}

db.insert("users", user["id"], user)

# Query by JSON path
dark_theme_users = db.query("users", "$.preferences.theme", "dark")

# Aggregate
total_users = db.aggregate("users", "$", "COUNT")
```

## Caching Solutions

### Redis-Compatible Cache

```python
import json
from typing import Any, Optional, Union, Dict
from datetime import timedelta
import time
import threading
from collections import OrderedDict

class CacheBackend:
    """In-memory cache backend with Redis-like interface"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict[str, tuple[Any, Optional[float]]] = OrderedDict()
        self.max_size = max_size
        self.lock = threading.RLock()
    
    def _expire_check(self, key: str) -> bool:
        """Check if key is expired"""
        if key in self.cache:
            value, expire_time = self.cache[key]
            if expire_time and time.time() > expire_time:
                del self.cache[key]
                return True
        return False
    
    def _evict_lru(self):
        """Evict least recently used items"""
        while len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        with self.lock:
            if self._expire_check(key):
                return None
            
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                value, _ = self.cache[key]
                return value
            
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value with optional TTL in seconds"""
        with self.lock:
            expire_time = time.time() + ttl if ttl else None
            
            # Remove if exists to update position
            if key in self.cache:
                del self.cache[key]
            
            # Evict if needed
            self._evict_lru()
            
            # Add to end
            self.cache[key] = (value, expire_time)
    
    def delete(self, key: str) -> bool:
        """Delete key"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        with self.lock:
            # Simple pattern matching
            if pattern == "*":
                return list(self.cache.keys())
            
            # Basic glob pattern
            import fnmatch
            return [k for k in self.cache.keys() if fnmatch.fnmatch(k, pattern)]

class KajsonCache:
    """Cache with automatic Kajson serialization"""
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
    
    def get(self, key: str, model_class: Optional[type] = None) -> Optional[Any]:
        """Get and deserialize value"""
        data = self.backend.get(key)
        if data is None:
            return None
        
        # Deserialize
        value = kajson.loads(data)
        
        # Convert to model if specified
        if model_class and isinstance(value, dict):
            return model_class(**value)
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None):
        """Serialize and set value"""
        # Convert timedelta to seconds
        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())
        
        # Serialize
        data = kajson.dumps(value)
        
        self.backend.set(key, data, ttl)
    
    def get_or_set(self, key: str, factory: callable, ttl: Optional[Union[int, timedelta]] = None) -> Any:
        """Get value or compute and set if missing"""
        value = self.get(key)
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        return value
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys = self.backend.keys(pattern)
        for key in keys:
            self.backend.delete(key)

# Usage
cache_backend = CacheBackend(max_size=100)
cache = KajsonCache(cache_backend)

# Cache Pydantic models
class Article(BaseModel):
    id: str
    title: str
    content: str
    author: str
    published_at: datetime
    view_count: int = 0

# Set with TTL
article = Article(
    id="article-1",
    title="Caching with Kajson",
    content="Learn how to cache complex objects...",
    author="Alice",
    published_at=datetime.now()
)

cache.set(f"article:{article.id}", article, ttl=timedelta(hours=1))

# Get with type
cached_article = cache.get(f"article:{article.id}", Article)

# Get or compute
def fetch_article_from_db(article_id: str) -> Article:
    # Simulate database fetch
    return Article(
        id=article_id,
        title="Fetched from DB",
        content="...",
        author="Bob",
        published_at=datetime.now()
    )

article = cache.get_or_set(
    "article:2",
    lambda: fetch_article_from_db("2"),
    ttl=timedelta(minutes=30)
)
```

## Data Migration

```python
from typing import Dict, Any, List, Callable
from abc import ABC, abstractmethod

class Migration(ABC):
    """Base class for data migrations"""
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Migration version"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Migration description"""
        pass
    
    @abstractmethod
    def up(self, data: Any) -> Any:
        """Apply migration"""
        pass
    
    @abstractmethod
    def down(self, data: Any) -> Any:
        """Rollback migration"""
        pass

class DataMigrator:
    """Handles data migrations"""
    
    def __init__(self, migrations: List[Migration]):
        self.migrations = sorted(migrations, key=lambda m: m.version)
        self.applied_migrations: List[str] = []
    
    def get_current_version(self, data: Any) -> Optional[str]:
        """Get current data version"""
        if isinstance(data, dict):
            return data.get("_version")
        return None
    
    def set_version(self, data: Any, version: str) -> Any:
        """Set data version"""
        if isinstance(data, dict):
            data["_version"] = version
        return data
    
    def migrate_to(self, data: Any, target_version: str) -> Any:
        """Migrate data to target version"""
        current_version = self.get_current_version(data) or "0.0.0"
        
        # Find migrations to apply
        migrations_to_apply = [
            m for m in self.migrations
            if m.version > current_version and m.version <= target_version
        ]
        
        # Apply migrations
        migrated_data = data
        for migration in migrations_to_apply:
            print(f"Applying migration {migration.version}: {migration.description}")
            migrated_data = migration.up(migrated_data)
            self.applied_migrations.append(migration.version)
        
        # Set final version
        if migrations_to_apply:
            migrated_data = self.set_version(migrated_data, target_version)
        
        return migrated_data
    
    def rollback_to(self, data: Any, target_version: str) -> Any:
        """Rollback data to target version"""
        current_version = self.get_current_version(data) or "999.999.999"
        
        # Find migrations to rollback
        migrations_to_rollback = [
            m for m in reversed(self.migrations)
            if m.version <= current_version and m.version > target_version
        ]
        
        # Rollback migrations
        migrated_data = data
        for migration in migrations_to_rollback:
            print(f"Rolling back migration {migration.version}")
            migrated_data = migration.down(migrated_data)
        
        # Set final version
        if migrations_to_rollback:
            migrated_data = self.set_version(migrated_data, target_version)
        
        return migrated_data

# Example migrations
class AddUserRolesMigration(Migration):
    @property
    def version(self) -> str:
        return "1.1.0"
    
    @property
    def description(self) -> str:
        return "Add roles field to users"
    
    def up(self, data: Any) -> Any:
        if "users" in data:
            for user in data["users"]:
                if "roles" not in user:
                    user["roles"] = ["user"]  # Default role
        return data
    
    def down(self, data: Any) -> Any:
        if "users" in data:
            for user in data["users"]:
                user.pop("roles", None)
        return data

class RenameFieldMigration(Migration):
    @property
    def version(self) -> str:
        return "1.2.0"
    
    @property
    def description(self) -> str:
        return "Rename 'username' to 'display_name'"
    
    def up(self, data: Any) -> Any:
        if "users" in data:
            for user in data["users"]:
                if "username" in user:
                    user["display_name"] = user.pop("username")
        return data
    
    def down(self, data: Any) -> Any:
        if "users" in data:
            for user in data["users"]:
                if "display_name" in user:
                    user["username"] = user.pop("display_name")
        return data

# Usage
migrations = [
    AddUserRolesMigration(),
    RenameFieldMigration()
]

migrator = DataMigrator(migrations)

# Load old data
with open("data/old_format.json", "r") as f:
    old_data = kajson.load(f)

# Migrate to latest version
new_data = migrator.migrate_to(old_data, "1.2.0")

# Save migrated data
with open("data/new_format.json", "w") as f:
    kajson.dump(new_data, f, indent=2)
```

## Backup and Restore

```python
import tarfile
import gzip
from datetime import datetime
import tempfile

class BackupManager:
    """Manage data backups with compression"""
    
    def __init__(self, backup_dir: str):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, data: Any, name: str = "backup") -> str:
        """Create compressed backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name}_{timestamp}"
        
        # Create temp directory for backup files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save data
            data_file = temp_path / "data.json"
            with open(data_file, "w") as f:
                kajson.dump(data, f, indent=2)
            
            # Save metadata
            metadata = {
                "backup_name": backup_name,
                "timestamp": datetime.now(),
                "data_size": data_file.stat().st_size,
                "format_version": "1.0"
            }
            
            metadata_file = temp_path / "metadata.json"
            with open(metadata_file, "w") as f:
                kajson.dump(metadata, f, indent=2)
            
            # Create compressed archive
            archive_path = self.backup_dir / f"{backup_name}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(data_file, arcname="data.json")
                tar.add(metadata_file, arcname="metadata.json")
        
        return str(archive_path)
    
    def restore_backup(self, backup_path: str) -> Any:
        """Restore from backup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract archive
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(temp_path)
            
            # Load metadata
            with open(temp_path / "metadata.json", "r") as f:
                metadata = kajson.load(f)
            
            print(f"Restoring backup: {metadata['backup_name']}")
            print(f"Created: {metadata['timestamp']}")
            
            # Load data
            with open(temp_path / "data.json", "r") as f:
                data = kajson.load(f)
            
            return data
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            # Extract metadata without full extraction
            with tarfile.open(backup_file, "r:gz") as tar:
                try:
                    metadata_member = tar.getmember("metadata.json")
                    metadata_file = tar.extractfile(metadata_member)
                    if metadata_file:
                        metadata = kajson.loads(metadata_file.read())
                        metadata["file_path"] = str(backup_file)
                        metadata["file_size"] = backup_file.stat().st_size
                        backups.append(metadata)
                except KeyError:
                    # Skip invalid backups
                    pass
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)
    
    def auto_cleanup(self, keep_days: int = 30):
        """Remove old backups"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for backup in self.list_backups():
            backup_date = backup["timestamp"]
            if isinstance(backup_date, str):
                backup_date = datetime.fromisoformat(backup_date)
            
            if backup_date < cutoff_date:
                Path(backup["file_path"]).unlink()
                print(f"Removed old backup: {backup['backup_name']}")

# Usage
backup_mgr = BackupManager("backups")

# Create backup
app_data = {
    "users": [...],
    "settings": {...},
    "stats": {...}
}

backup_path = backup_mgr.create_backup(app_data, "app_state")

# List backups
for backup in backup_mgr.list_backups():
    print(f"{backup['backup_name']} - {backup['timestamp']}")

# Restore from backup
restored_data = backup_mgr.restore_backup(backup_path)

# Auto cleanup old backups
backup_mgr.auto_cleanup(keep_days=7)
```

## Best Practices

1. **Always validate data** before persistence using Pydantic models
2. **Use transactions** when available for data consistency
3. **Implement proper locking** for concurrent access
4. **Version your data format** to support migrations
5. **Create regular backups** especially before migrations
6. **Monitor storage size** and implement cleanup strategies
7. **Use appropriate storage** for your use case (files, database, cache)
8. **Handle errors gracefully** with proper logging

## See Also

- [Configuration Files](config-files.md) - Configuration persistence patterns
- [Error Handling](../guide/error-handling.md) - Handling persistence errors
- [Custom Types](../guide/custom-types.md) - Persisting custom objects
