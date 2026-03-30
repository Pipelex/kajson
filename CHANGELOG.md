# Changelog

## [v0.4.0] - 2026-03-30

### Added
 - **Class Registry Support:** Added an optional `class_registry` parameter to `kajson.loads()` and `kajson.load()`, enabling resolution of dynamically generated classes by checking a provided registry before falling back to `sys.modules`.
 - **Python 3.14 Support:** Added official support, CI testing, and package classifiers for Python 3.14 (including prereleases).
 - **CI/Agent Makefile Targets:** Added `agent-check` and `agent-test` targets to the `Makefile` to streamline CI pipeline execution.

### Changed
 - **Python Version Support:** The minimum required Python version has been increased from 3.9 to **3.10**. Python 3.9 support, CI testing, and classifiers have been removed. All documentation, examples, and package metadata have been updated accordingly.
 - **CI Pipeline Updates:** Updated GitHub Actions workflows to use `actions/setup-python@v5`, adjusted the testing matrix to cover Python 3.10–3.14, and simplified the CLA workflow to use a direct Personal Access Token instead of dynamically generating a GitHub App token.
 - **Decoder Refactoring:** Extracted `_apply_decoder_strategies` method in `UniversalJSONDecoder` for cleaner, more maintainable decoding logic.
 - **Copyright Updates:** Updated copyright notices across the codebase to 2025–2026.

### Fixed
 - **Dynamic Class Decoding:** Fixed decoding of dynamically generated classes (which often default to `__module__ = 'builtins'`) by prioritizing the explicit `class_registry` over the `sys.modules` fallback.
 - **Type Checking:** Added a missing type cast for `RootModel` instantiation in `UniversalJSONDecoder` to satisfy strict type checkers.

## [v0.3.2] - 2025-11-24

### 🚀 New Features

- **GitHub Issue Templates**: Added bug report, feature request, and general issue templates to GitHub repository for better issue management
- **API Documentation**: Added KajsonManager API reference documentation (Issue #26)

### 📝 Changes

- **Makefile Updates**: Renamed 'doc' targets to 'docs', including 'docs-check' and 'docs-deploy' for better consistency
- **UniversalJSONEncoder Cleanup**: Removed unused logger from UniversalJSONEncoder class (Issue #27)
- **Performance Fix**: In json_encoder.py, in _get_type_module(), the regex compilation should be at the module level (#28)

### 🔒 Security

- **Documentation**: Added security considerations section to README regarding deserializing untrusted JSON data

## [v0.3.1] - 2025-07-10

- Fix documentation URL in `pyproject.toml`
- Add GHA for doc deploy

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
