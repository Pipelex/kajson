# Installation

Kajson requires Python 3.10 or higher and can be installed using your favorite package manager.

## Requirements

- Python ≥ 3.10
- Pydantic v2 (installed automatically)

## Installation Methods

### Using pip

```bash
pip install kajson
```

### Using poetry

```bash
poetry add kajson
```

### Using uv (recommended)

```bash
uv pip install kajson
```

## Development Installation

If you want to contribute to Kajson or install from source:

```bash
# Clone the repository
git clone https://github.com/Pipelex/kajson.git
cd kajson

# Install with development dependencies
make install
```

The development interpreter is the Python version that `.python-version` names at the repository root, and `make install` builds `.venv` on it. If `.venv` was built on another Python, the next `make install` rebuilds it on the pinned version. To try another version, run `PYTHON_VERSION=3.13 make install` with the version you want; a plain `make install` afterwards returns `.venv` to the pin. CI runs the checks and tests on every Python version kajson supports.

## Verify Installation

After installation, you can verify that Kajson is properly installed:

```python
import kajson

# Check version
print(kajson.__version__)

# Test basic functionality
data = {"message": "Hello, Kajson!"}
json_str = kajson.dumps(data)
print(json_str)
```

## Next Steps

Once installed, check out the [Quick Start Guide](quick-start.md) to begin using Kajson in your projects. 
