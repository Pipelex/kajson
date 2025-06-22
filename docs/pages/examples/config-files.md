# Configuration Files

This example demonstrates how to use Kajson for managing application configuration with type safety, validation, and environment-specific settings.

## Basic Configuration Management

### Simple Configuration Model

```python
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import kajson
import os
from pathlib import Path

class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    database: str
    username: str
    password: str
    pool_size: int = Field(default=10, ge=1, le=100)
    timeout: timedelta = timedelta(seconds=30)
    ssl_enabled: bool = False
    
    @validator('password')
    def password_not_empty(cls, v):
        if not v:
            raise ValueError('Database password cannot be empty')
        return v

class CacheConfig(BaseModel):
    backend: str = Field(default="redis", pattern="^(redis|memcached|memory)$")
    host: str = "localhost"
    port: int = 6379
    ttl: timedelta = timedelta(hours=1)
    key_prefix: str = "myapp:"

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[Path] = None
    max_file_size: int = Field(default=10485760, description="Max log file size in bytes")
    backup_count: int = Field(default=5, ge=0)

class AppConfig(BaseModel):
    app_name: str
    version: str = "1.0.0"
    debug: bool = False
    secret_key: str
    allowed_hosts: List[str] = ["localhost"]
    
    database: DatabaseConfig
    cache: Optional[CacheConfig] = None
    logging: LoggingConfig = LoggingConfig()
    
    # Feature flags
    features: Dict[str, bool] = {}
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: Optional[datetime] = None
    
    class Config:
        validate_assignment = True

# Load configuration
def load_config(config_path: str = "config.json") -> AppConfig:
    """Load configuration from file"""
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, "r") as f:
        data = kajson.load(f)
    
    return data if isinstance(data, AppConfig) else AppConfig(**data)

# Save configuration
def save_config(config: AppConfig, config_path: str = "config.json"):
    """Save configuration to file"""
    config.last_modified = datetime.now()
    
    with open(config_path, "w") as f:
        kajson.dump(config, f, indent=2, sort_keys=True)
```

### Environment-Specific Configuration

```python
import os
from typing import Optional, Dict, Any
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

class EnvironmentConfig:
    def __init__(self, base_path: str = "config"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.env = self._detect_environment()
        self._config: Optional[AppConfig] = None
    
    def _detect_environment(self) -> Environment:
        """Detect current environment"""
        env_var = os.getenv("APP_ENV", "development").lower()
        try:
            return Environment(env_var)
        except ValueError:
            print(f"Unknown environment '{env_var}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _get_config_path(self, env: Optional[Environment] = None) -> Path:
        """Get configuration file path for environment"""
        env = env or self.env
        return self.base_path / f"config.{env.value}.json"
    
    def load(self) -> AppConfig:
        """Load configuration for current environment"""
        if self._config is not None:
            return self._config
        
        # Load base configuration
        base_config_path = self.base_path / "config.base.json"
        if base_config_path.exists():
            with open(base_config_path, "r") as f:
                base_data = kajson.load(f)
        else:
            base_data = {}
        
        # Load environment-specific configuration
        env_config_path = self._get_config_path()
        if env_config_path.exists():
            with open(env_config_path, "r") as f:
                env_data = kajson.load(f)
        else:
            env_data = {}
        
        # Merge configurations (env overrides base)
        merged_data = self._deep_merge(base_data, env_data)
        
        # Apply environment variable overrides
        merged_data = self._apply_env_overrides(merged_data)
        
        self._config = AppConfig(**merged_data)
        return self._config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        # Example: APP_DATABASE_HOST overrides config.database.host
        for key, value in os.environ.items():
            if key.startswith("APP_"):
                config_key = key[4:].lower().replace("_", ".")
                self._set_nested(config, config_key, value)
        
        return config
    
    def _set_nested(self, data: Dict[str, Any], key: str, value: str):
        """Set nested dictionary value using dot notation"""
        keys = key.split(".")
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Convert value to appropriate type
        current[keys[-1]] = self._parse_value(value)
    
    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type"""
        # Try to parse as JSON first
        try:
            return kajson.loads(value)
        except:
            pass
        
        # Boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        
        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        return value
    
    def save(self, env: Optional[Environment] = None):
        """Save current configuration"""
        if self._config is None:
            raise ValueError("No configuration loaded")
        
        config_path = self._get_config_path(env)
        save_config(self._config, str(config_path))
    
    def reload(self):
        """Reload configuration from disk"""
        self._config = None
        return self.load()

# Usage
env_config = EnvironmentConfig()
config = env_config.load()

print(f"Running in {env_config.env.value} mode")
print(f"Database: {config.database.host}:{config.database.port}")
```

## Configuration Validation and Defaults

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any
import re

class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str
    smtp_password: str
    use_tls: bool = True
    from_address: str
    from_name: str = "MyApp"
    
    @validator('from_address')
    def validate_email(cls, v):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Invalid email address')
        return v

class SecurityConfig(BaseModel):
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = Field(default=24, ge=1)
    
    password_min_length: int = Field(default=8, ge=6)
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    @validator('jwt_secret_key')
    def validate_secret_key(cls, v):
        if v == "change-me" or len(v) < 32:
            raise ValueError(
                'JWT secret key must be at least 32 characters and not the default value'
            )
        return v
    
    @root_validator
    def validate_password_requirements(cls, values):
        min_length = values.get('password_min_length', 8)
        requirements = sum([
            values.get('password_require_uppercase', False),
            values.get('password_require_lowercase', False),
            values.get('password_require_numbers', False),
            values.get('password_require_special', False)
        ])
        
        if requirements == 0:
            raise ValueError('At least one password requirement must be enabled')
        
        return values

class RateLimitConfig(BaseModel):
    enabled: bool = True
    requests_per_minute: int = Field(default=60, ge=1)
    requests_per_hour: int = Field(default=1000, ge=1)
    burst_size: int = Field(default=10, ge=1)
    
    @root_validator
    def validate_limits(cls, values):
        rpm = values.get('requests_per_minute', 60)
        rph = values.get('requests_per_hour', 1000)
        
        if rpm * 60 > rph:
            raise ValueError(
                'requests_per_minute * 60 cannot exceed requests_per_hour'
            )
        
        return values

# Configuration with computed properties
class AdvancedConfig(BaseModel):
    environment: Environment
    base_url: str
    
    email: EmailConfig
    security: SecurityConfig
    rate_limit: RateLimitConfig
    
    # Computed properties
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_production:
            return [self.base_url]
        return self.security.allowed_origins
    
    @property
    def debug_enabled(self) -> bool:
        """Debug is only enabled in development"""
        return self.environment == Environment.DEVELOPMENT
    
    def get_database_url(self, include_password: bool = False) -> str:
        """Generate database connection URL"""
        db = self.database
        password = db.password if include_password else "***"
        return f"postgresql://{db.username}:{password}@{db.host}:{db.port}/{db.database}"
```

## Configuration Hot Reloading

```python
import asyncio
from pathlib import Path
from typing import Callable, List, Optional
import hashlib
from datetime import datetime

class ConfigWatcher:
    def __init__(self, config_path: str, check_interval: float = 1.0):
        self.config_path = Path(config_path)
        self.check_interval = check_interval
        self.callbacks: List[Callable[[AppConfig], None]] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_hash: Optional[str] = None
        self._config: Optional[AppConfig] = None
    
    def add_callback(self, callback: Callable[[AppConfig], None]):
        """Add callback to be called when configuration changes"""
        self.callbacks.append(callback)
    
    def _get_file_hash(self) -> str:
        """Get hash of configuration file"""
        with open(self.config_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    
    async def _watch_loop(self):
        """Main watch loop"""
        while self._running:
            try:
                if self.config_path.exists():
                    current_hash = self._get_file_hash()
                    
                    if current_hash != self._last_hash:
                        self._last_hash = current_hash
                        
                        # Load new configuration
                        with open(self.config_path, "r") as f:
                            new_config = kajson.load(f)
                        
                        if isinstance(new_config, dict):
                            new_config = AppConfig(**new_config)
                        
                        self._config = new_config
                        
                        # Call callbacks
                        for callback in self.callbacks:
                            try:
                                callback(new_config)
                            except Exception as e:
                                print(f"Error in config callback: {e}")
                
            except Exception as e:
                print(f"Error watching config file: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def start(self):
        """Start watching configuration file"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._watch_loop())
    
    async def stop(self):
        """Stop watching configuration file"""
        self._running = False
        if self._task:
            await self._task
    
    @property
    def config(self) -> Optional[AppConfig]:
        """Get current configuration"""
        return self._config

# Usage example
async def on_config_change(config: AppConfig):
    """Handle configuration changes"""
    print(f"Configuration updated at {datetime.now()}")
    print(f"Debug mode: {config.debug}")
    print(f"Database: {config.database.host}")
    
    # Reconnect to database, update caches, etc.

async def main():
    # Create watcher
    watcher = ConfigWatcher("config.json")
    watcher.add_callback(on_config_change)
    
    # Start watching
    watcher.start()
    
    # Simulate running application
    try:
        await asyncio.sleep(60)  # Run for 60 seconds
    finally:
        await watcher.stop()

# Run with: asyncio.run(main())
```

## Configuration Schema Generation

```python
from typing import Dict, Any, Type
from pydantic import BaseModel
import kajson

def generate_config_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """Generate JSON schema for configuration model"""
    return model.schema()

def generate_example_config(model: Type[BaseModel]) -> str:
    """Generate example configuration file"""
    schema = model.schema()
    
    def get_example_value(field_schema: Dict[str, Any]) -> Any:
        """Get example value for field"""
        if "example" in field_schema:
            return field_schema["example"]
        elif "default" in field_schema:
            return field_schema["default"]
        elif field_schema.get("type") == "string":
            return "example-string"
        elif field_schema.get("type") == "integer":
            return 42
        elif field_schema.get("type") == "boolean":
            return True
        elif field_schema.get("type") == "array":
            return []
        elif field_schema.get("type") == "object":
            return {}
        else:
            return None
    
    example_data = {}
    
    for field_name, field_info in schema.get("properties", {}).items():
        if "$ref" in field_info:
            # Handle nested models
            ref_name = field_info["$ref"].split("/")[-1]
            if ref_name in schema.get("definitions", {}):
                nested_schema = schema["definitions"][ref_name]
                nested_example = {}
                for nested_field, nested_info in nested_schema.get("properties", {}).items():
                    nested_example[nested_field] = get_example_value(nested_info)
                example_data[field_name] = nested_example
        else:
            example_data[field_name] = get_example_value(field_info)
    
    return kajson.dumps(example_data, indent=2)

# Generate configuration template
def create_config_template(output_path: str = "config.template.json"):
    """Create a configuration template file"""
    schema = generate_config_schema(AppConfig)
    example = generate_example_config(AppConfig)
    
    template = {
        "$schema": schema,
        "$comment": "This is a configuration template. Copy to config.json and modify as needed.",
        "example": kajson.loads(example)
    }
    
    with open(output_path, "w") as f:
        kajson.dump(template, f, indent=2)
    
    print(f"Configuration template created: {output_path}")

# Validate configuration against schema
def validate_config_file(config_path: str) -> bool:
    """Validate configuration file"""
    try:
        config = load_config(config_path)
        print(f"✓ Configuration is valid")
        print(f"  App: {config.app_name} v{config.version}")
        print(f"  Environment: {config.debug and 'Debug' or 'Production'}")
        return True
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False
```

## Configuration Migration

```python
from typing import Dict, Any, Callable
import shutil
from datetime import datetime

class ConfigMigration:
    def __init__(self, version: str, migrate_func: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.version = version
        self.migrate_func = migrate_func

class ConfigMigrator:
    def __init__(self):
        self.migrations: List[ConfigMigration] = []
    
    def add_migration(self, version: str):
        """Decorator to add migration"""
        def decorator(func: Callable[[Dict[str, Any]], Dict[str, Any]]):
            self.migrations.append(ConfigMigration(version, func))
            return func
        return decorator
    
    def migrate(self, config_path: str, target_version: str):
        """Migrate configuration to target version"""
        # Backup current configuration
        backup_path = f"{config_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(config_path, backup_path)
        print(f"Created backup: {backup_path}")
        
        # Load current configuration
        with open(config_path, "r") as f:
            config_data = kajson.load(f)
        
        current_version = config_data.get("version", "1.0.0")
        
        # Apply migrations
        for migration in self.migrations:
            if self._version_compare(current_version, migration.version) < 0 <= self._version_compare(migration.version, target_version):
                print(f"Applying migration to v{migration.version}")
                config_data = migration.migrate_func(config_data)
                config_data["version"] = migration.version
        
        # Save migrated configuration
        with open(config_path, "w") as f:
            kajson.dump(config_data, f, indent=2)
        
        print(f"Configuration migrated to v{target_version}")
    
    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare version strings"""
        v1_parts = [int(x) for x in v1.split(".")]
        v2_parts = [int(x) for x in v2.split(".")]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            p1 = v1_parts[i] if i < len(v1_parts) else 0
            p2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        
        return 0

# Example migrations
migrator = ConfigMigrator()

@migrator.add_migration("1.1.0")
def migrate_to_1_1_0(config: Dict[str, Any]) -> Dict[str, Any]:
    """Add cache configuration"""
    if "cache" not in config:
        config["cache"] = {
            "backend": "redis",
            "host": "localhost",
            "port": 6379,
            "ttl": 3600
        }
    return config

@migrator.add_migration("1.2.0")
def migrate_to_1_2_0(config: Dict[str, Any]) -> Dict[str, Any]:
    """Restructure database configuration"""
    if "database" in config and isinstance(config["database"], dict):
        if "connection_string" in config["database"]:
            # Parse connection string into components
            # This is a simplified example
            config["database"] = {
                "host": "localhost",
                "port": 5432,
                "database": "myapp",
                "username": "user",
                "password": "password"
            }
    return config
```

## Best Practices

1. **Use type-safe models** with Pydantic for configuration validation
2. **Support environment overrides** for deployment flexibility
3. **Validate configuration** on load to catch errors early
4. **Provide defaults** for optional configuration values
5. **Keep secrets separate** from main configuration files
6. **Version your configuration** to support migrations
7. **Document configuration options** with field descriptions
8. **Use configuration templates** for easy setup

## See Also

- [Data Persistence](data-persistence.md) - Storing configuration in databases
- [Pydantic Integration](../guide/pydantic.md) - Advanced validation
- [Error Handling](../guide/error-handling.md) - Configuration error handling
