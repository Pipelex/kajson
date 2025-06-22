# Contributing to kajson

Thank you for your interest in kajson! While kajson is a stable and feature-complete library, we do accept contributions if you find bugs or have improvements to suggest.

kajson is a powerful drop-in replacement for Python's standard `json` module that automatically handles complex object serialization, including Pydantic v2 models, datetime objects, and custom types. The library is maintained by the same team that develops Pipelex.

Everyone interacting in codebases, issue trackers, mailing lists, or any other kajson activities is expected to follow the [Code of Conduct](docs/CODE_OF_CONDUCT.md). Please review it before getting started.

If you have questions or want to discuss potential contributions, feel free to join our community on Discord in the #code-contributions channel.

Most of the issues that are open for contributions are tagged with `good first issue` or `help-welcome`. If you see an issue that isn't tagged that you're interested in, post a comment with your approach, and we'll be happy to assign it to you. If you submit a fix that isn't linked to an issue you're assigned, there's a chance it won't be accepted. Don't hesitate to open an issue to discuss your ideas before getting to work.

Since kajson is a mature library, most contributions will likely be:

- **Bug fixes**: Edge cases in serialization/deserialization
- **Type support**: Adding support for additional third-party library types
- **Documentation**: Improving examples and clarifications
- **Performance**: Optimizations that don't break existing functionality

## Contribution process

- Fork the [kajson repository](https://github.com/PipelexLab/kajson)
- Clone the repository locally
- Install dependencies: `make install` (creates .venv and installs dependencies)
- Run checks to make sure all is good: `make check` & `make test`
- Create a branch with the format `user_name/category/short_slug` where category is one of: `feature`, `fix`, `refactor`, `docs`, `cicd` or `chore`
- Make and commit changes
- Push your local branch to your fork
- Open a PR that [links to an existing Issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue) which does not include the `needs triage` label
- Write a PR title and description by filling the template
- CI tests will be triggered and maintainers will review the code
- Respond to feedback if required
- Merge the contribution

## Requirements

- Python ≥ 3.9
- uv ≥ 0.7.2

## Development Setup

- Fork & clone the repository
- Run `make install` to set up virtualenv and dependencies
- Use uv for dependency management:
  - Runtime deps: `uv add <package>`
  - Dev deps: `uv add --dev <package>`
  - Keep dependencies alphabetically ordered in pyproject.toml

## Available Make Commands

```bash
# Setup
make install              # Create local virtualenv & install all dependencies
make update              # Upgrade dependencies via uv
make build               # Build the wheels

# Code Quality
make check               # Run format, lint, mypy, and pyright
make format              # Format with ruff
make lint                # Lint with ruff
make pyright            # Check types with pyright
make mypy               # Check types with mypy
make fix-unused-imports # Fix unused imports

# Testing
make test               # Run unit tests
make tp                 # Run tests with prints (useful for debugging)
make cov                # Run tests with coverage
make cm                 # Run tests with coverage and missing lines

# Documentation
make doc                # Serve documentation locally with mkdocs
make doc-check          # Check documentation build
make doc-deploy         # Deploy documentation to GitHub Pages

# Cleanup
make cleanall           # Remove all derived files and virtual env
```

## Pull Request Process

1. Fork the kajson repository
2. Clone the repository locally
3. Install dependencies: `make install`
4. Run checks to ensure everything works: `make check` & `make test`
5. Create a branch for your feature/bug-fix with the format `user_name/feature/some_feature` or `user_name/fix/some_bugfix`
6. Make and commit changes
7. Write tests for your changes (kajson aims for high test coverage)
8. When ready, run quality checks:
   - Run `make fix-unused-imports` to remove unused imports
   - Run `make check` for formatting, linting, and type-checking
   - Run `make test` to ensure all tests pass
9. Push your local branch to your fork
10. Open a PR that links to an existing issue
11. Fill out the PR template with a clear description
12. Mark as Draft until CI passes
13. Maintainers will review the code
14. Respond to feedback if required
15. Once approved, your contribution will be merged

## Code Style

- We use `ruff` for formatting and linting
- Type hints are required for all new code
- Follow existing patterns in the codebase
- Document complex logic with comments
- Add docstrings to all public functions and classes

## Testing Guidelines

- Write tests for all new functionality
- Tests should be in the `tests/` directory
- Use pytest for all tests
- Aim for high test coverage
- Test edge cases and error conditions
- Integration tests for encoder/decoder combinations are especially valuable

## Adding New Type Support

When adding support for new types:

1. Create encoder and decoder functions
2. Register them in the appropriate registry
3. Add comprehensive tests including:
   - Basic serialization/deserialization
   - Nested structures
   - Edge cases (None, empty, special values)
   - Error handling
4. Update documentation with usage examples

## License

* **CLA** – The first time you open a PR, the CLA-assistant bot will guide you through signing the Contributor License Agreement. The process uses the [CLA assistant lite](https://github.com/marketplace/actions/cla-assistant-lite).
* **Code of Conduct** – Be kind. All interactions fall under [`docs/CODE_OF_CONDUCT.md`](docs/CODE_OF_CONDUCT.md).
* **License** – kajson is licensed under the [Apache 2.0 License](LICENSE).
