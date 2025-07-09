# Changelog

## [v0.3.0] - 2025-07-09

- Making `KajsonManager` a proper Singleton using `MetaSingleton`

## [v0.2.4] - 2025-06-30

- Automatic changelog in Github Release

## [v0.2.3] - 2025-06-26

- Better handle enums including in pydantic BaseModels

## [v0.2.2] - 2025-06-26

### 🚀 New Features

- **Generic Pydantic Models**: Comprehensive support for generic models with type parameters (`Container[T]`, `KeyValueStore[K, V]`, etc.) with enhanced class registry that automatically handles generic type resolution and fallback to base classes
- **Cross-Platform DateTime**: Enhanced datetime encoding with 4-digit year formatting for better cross-platform compatibility

### 📚 New Examples

- `ex_15_pydantic_subclass_polymorphism.py`: Demonstrates polymorphic APIs, plugin architectures, and mixed collections with preserved subclass types
- `ex_16_generic_models.py`: Showcases single/multiple type parameters, nested generics, and bounded generic types

### 🏗️ Core Improvements

- **Automatic Metadata Handling**: Built-in encoders now automatically receive `__class__` and `__module__` metadata, simplifying custom encoder implementation
- **Generic Type Resolution**: JSON decoder now handles generic class names by intelligently falling back to base classes
- **Timezone Support**: Fixed missing timezone encoder/decoder registration for `ZoneInfo` objects
- **Simplified Encoders**: Removed manual metadata from built-in encoders (datetime, date, time, timedelta, timezone)

### 📖 Documentation

- **Expanded README**: Added compatibility matrix, migration guide, architecture overview, and comprehensive use cases
- **Enhanced API Docs**: Updated encoder/decoder documentation with automatic metadata handling examples
- **Examples Documentation**: New detailed examples with polymorphism and generic models patterns

### 🧪 Testing

- **Integration Tests**: Added comprehensive test suites for generic models and subclass polymorphism
- **DateTime Tests**: Enhanced datetime/timezone round-trip testing with edge cases and complex structures
- **Class Registry Tests**: Improved test coverage for dynamic class scenarios


## [v0.2.1] - 2025-06-24

- Added the last missing example & doc: using the class registry to handle dynamic classes from distributed systems and runtime generation
- Fixed markdown of overview docs

## [v0.2.0] - 2025-06-23

- Test coverage 100%
- New integration tests
- New examples in `examples/` directory, used as e2e tests
- Full documentation in `docs/` directory
- MkDocs deployed on GitHub pages: [https://pipelex.github.io/kajson/](https://pipelex.github.io/kajson/) 

## [v0.1.6] - 2025-01-02

- Introduced `ClassRegistryAbstract` (ABC) for dependency injection of ClassRegistry
- Added `KajsonManager` for better lifecycle management
- Changed default Python version to 3.11 (still requires Python >=3.9)
- Updated Pydantic dependency from exact version `==2.10.6` to minimum version `>=2.10.6`
- Code cleanup and removal of unused components, most notably the `sandbox_manager`

## [v0.1.5] - 2025-06-02

- Switch from `poetry` to `uv`
- The python required version is now `>=3.9`

## [v0.1.4] - 2025-05-25

- Remove inappropriate VS Code settings

## [v0.1.3] - 2025-05-16

- Addind `test_serde_union_discrim`

## [v0.1.2] - 2025-05-16

- Added pipelex github repository in `README.md`

## [v0.1.1] - 2025-05-12

- Fix description, `project.urls` and some other fields of `pyproject.toml`
- fix allowlist of CLA GHA

## [v0.1.0] - 2025-05-12

- Initial release 🎉
