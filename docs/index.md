---
title: "Kajson - Universal JSON Encoder/Decoder for Python"
---

# Welcome to Kajson Documentation

**Kajson** is a powerful drop-in replacement for Python's standard `json` module that automatically handles complex object serialization, including **Pydantic v2 models**, **datetime objects**, and **custom types**.

<div class="grid cards" markdown>

-   :material-rocket-launch-outline:{ .lg .middle } **Quick Start**

    ---

    Get up and running with Kajson in minutes

    [:octicons-arrow-right-24: Installation](pages/installation.md)
    [:octicons-arrow-right-24: Quick Start Guide](pages/quick-start.md)

-   :material-book-open-variant:{ .lg .middle } **Learn**

    ---

    Master Kajson's features with our comprehensive guides

    [:octicons-arrow-right-24: User Guide](pages/guide/overview.md)
    [:octicons-arrow-right-24: Examples](pages/examples/index.md)

-   :material-code-braces:{ .lg .middle } **API Reference**

    ---

    Detailed documentation of all Kajson functions and classes

    [:octicons-arrow-right-24: API Documentation](pages/api/kajson.md)

-   :material-github:{ .lg .middle } **Contribute**

    ---

    Help improve Kajson

    [:octicons-arrow-right-24: Contributing Guidelines](contributing.md)
    [:octicons-arrow-right-24: GitHub Repository](https://github.com/PipelexLab/kajson)

</div>

## Why Kajson?

Say goodbye to `type X is not JSON serializable`!

### The Problem with Standard JSON

```python
import json
from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    name: str
    created_at: datetime

user = User(name="Alice", created_at=datetime.now())

# ❌ Standard json fails
json.dumps(user)  # TypeError: Object of type User is not JSON serializable
```

### The Kajson Solution

```python
import kajson

# ✅ Just works!
json_str = kajson.dumps(user)
restored_user = kajson.loads(json_str)
assert user == restored_user  # Perfect reconstruction!
```

## Key Features

- **🔄 Drop-in replacement** - Same API as standard `json` module
- **🐍 Pydantic v2 support** - Seamless serialization of Pydantic models
- **📅 DateTime handling** - Built-in support for date, time, datetime, timedelta
- **🏗️ Type preservation** - Automatically preserves and reconstructs original types
- **🔌 Extensible** - Easy registration of custom encoders/decoders
- **🎁 Batteries included** - Common types work out of the box

## Installation

=== "pip"

    ```bash
    pip install kajson
    ```

=== "poetry"

    ```bash
    poetry add kajson
    ```

=== "uv"

    ```bash
    uv pip install kajson
    ```

## Basic Example

```python
from datetime import datetime, timedelta
from pydantic import BaseModel
import kajson

class Task(BaseModel):
    name: str
    created_at: datetime
    duration: timedelta

# Create and serialize
task = Task(
    name="Write documentation",
    created_at=datetime.now(),
    duration=timedelta(hours=2)
)

json_str = kajson.dumps(task, indent=2)
print(json_str)

# Deserialize back
restored_task = kajson.loads(json_str)
assert task == restored_task
```

## Used by Pipelex

This library is used by [Pipelex](https://github.com/Pipelex/pipelex), the open-source language for repeatable AI workflows.

## License

Kajson is distributed under the [Apache 2.0 License](license.md).

This project is based on the excellent work from [unijson](https://github.com/bpietropaoli/unijson) by Bastien Pietropaoli.
