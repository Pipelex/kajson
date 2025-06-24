# Changelog

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
