# Changelog

## [Unreleased]

### Fixed
- **`ClassRegistry.register_classes_dict({})` no longer raises `IndexError`.** The method chose its log line with an `nb_classes > 1` / `else` split, and the `else` arm assumed exactly one entry — so it indexed into the values of an empty dict and crashed before the caller learned anything had gone wrong. Registering nothing is a legitimate call (seeding a registry from a snapshot that happens to be empty, which is what a process-global registry looks like between a teardown and the next boot), and it is now a no-op that logs and returns, matching how `register_classes` has always handled an empty list. Callers that guard the call site against an empty dict can drop the guard.
- **A Sigstore outage can no longer cost a release its GitHub Release and tag.** The publish workflow signed the distributions before creating the release, and the tag only exists as a side effect of `gh release create` — so when the pinned `sigstore/gh-action-sigstore-python@v3.0.0` started failing deterministically against the refreshed Sigstore trust root (`root was signed by 0/3 keys`), the signing step took the whole job down *after* the package had already reached PyPI, leaving a published version with neither a release nor a tag. The fix: the action is bumped to v3.5.0 (SHA-pinned, matching the pin `pipelex` already carries and the one allowed by the enterprise Actions allowlist); the release is now created and the distributions attached *before* signing, with signing marked `continue-on-error` and the signature upload gated on it succeeding, so attestation is a nice-to-have rather than a gate on the record of what shipped; and the recovery path the warning points at was made real, which took more than the idempotent release step alone — the release step now edits an existing release instead of failing on it, the PyPI publish step passes `skip-existing` so a re-run is not rejected for republishing an immutable version (an unbumped version is still caught by the version check on the PR), and the signature upload is scoped to the `.sigstore.json` bundles instead of everything in `dist/`, since `--clobber` deletes an asset before replacing it and the wider glob put the freshly attached distributions back at risk. An unsigned release is reported as a workflow warning naming the re-run that works.

### Changed
- **Tooling:** Pinned `ruff` to an exact `0.16.4`, replacing the `>=0.6.8` floor. The exact pin matches what the Ruff VS Code extension now bundles, which matters because Ruff 0.16 lints `pyproject.toml` itself: the extension syncs the config file to the language server, and a pre-0.16 binary parses it as Python source and paints phantom `invalid-syntax` diagnostics on lines like `requires-python`. A floor let the editor and the CLI resolve to different binaries; an exact pin cannot. This is a dev dependency, so no shipped behaviour changes, and the upgrade produced no new lint findings.
- **Docs:** Reformatted the Python examples throughout the documentation and the README. Ruff 0.16 formats Python code blocks embedded in Markdown, which it previously left alone, so the examples now follow the same formatter rules as the source tree — blank lines around top-level definitions and the project's line length applied to call and literal wrapping. Only formatting changed; every example does the same thing it did before, and the strict mkdocs build still passes.
- **Editor config:** Removed the `ruff.configuration` entry from `.vscode/settings.json`. That setting takes a path to a config file rather than a CLI flag, so its `--config=pyproject.toml` value never resolved — it only appeared to work because Ruff falls back to discovering the same `pyproject.toml` on its own.

## [v0.7.0] - 2026-06-10

### Fixed
- **Aware datetimes now decode without an external timezone database.** kajson serialized timezone-aware datetimes into a format its own decoder could not read on hosts with neither system tz files (`/usr/share/zoneinfo`) nor the `tzdata` package — e.g. uv-managed python-build-standalone interpreters on bare containers, or Windows. Decoding any aware datetime (including plain UTC) raised `KajsonDecoderError` wrapping `ZoneInfoNotFoundError`. Two complementary fixes: (1) `tzdata` is now a declared dependency, so a tz database is always available; (2) the wire format is now self-sufficient — see below.
- **Fixed-offset timezones round-trip.** `datetime.timezone` tzinfos (e.g. from `datetime.fromisoformat("...+02:00")`) encoded as non-IANA names like `"UTC+02:00"` that decode could never resolve, so they failed on every host regardless of tzdata. They now round-trip correctly, preserving custom names passed to the `timezone` constructor. Legacy payloads carrying `"UTC+02:00"`-style names (which never decoded before) now decode too.
- **`datetime.time` with `datetime.timezone` tzinfo is serializable.** `json_encode_time` embedded the raw tzinfo object instead of a string; a `time` at `timezone.utc` raised `TypeError` at encode time. The time codec now uses the same name + offset wire format as the datetime codec. Legacy time payloads (nested ZoneInfo dict) still decode.
- **DST fall-back (`fold=1`) datetimes keep their instant.** The wire offset is authoritative when decoding: for an ambiguous wall time the decoder restores the fold the encoder saw, and when a tzinfo name contradicts the offset (a fixed offset labeled with an IANA key like `timezone(timedelta(hours=1), "CET")` — `CET` is a real tzdata key — or tz rules that changed since encoding) it falls back to the fixed offset, name preserved. Previously such payloads silently decoded to a different instant. The same reasoning fixes aware `time` values: a non-null offset on a time payload proves a fixed-offset origin, so the name is never resolved through `ZoneInfo` (which would destroy the offset).

### Added
- **Self-sufficient timezone wire format.** Datetime and time payloads now carry an additive `utcoffset` field (seconds) alongside the tzinfo name. Decoding prefers the named zone (`ZoneInfo`) to preserve DST semantics — reconciled against the authoritative wire offset, see above — special-cases `"UTC"`/offset-0 to `datetime.timezone.utc` with zero tz-database dependence, and degrades gracefully to a fixed-offset `datetime.timezone` (keeping the original name) when the name cannot be resolved. One inherent exception: a `datetime.time` with a named zone (`ZoneInfo`) has no defined offset without a date, so its payload carries only the name and decoding it still requires a timezone database. Old payloads (no `utcoffset` field) still decode. New payloads decode on older kajson versions for datetimes (the extra key is ignored), with two exceptions: a `time` with a `ZoneInfo` tzinfo now encodes the zone as a string, which kajson <= 0.6.0 cannot decode (it expected a nested tzinfo object), and bare `datetime.timezone` payloads decode as plain dicts on old versions (they had no decoder for them). In a mixed-version fleet, upgrade consumers before producers.
- **Encoder/decoder for `datetime.timezone`.** Bare fixed-offset timezone objects (including `timezone.utc`) now serialize and round-trip.
- **CI coverage for tz-database-less hosts.** The test suite runs a second time with `PYTHONTZPATH=/nonexistent`, plus an in-process fixture simulates the complete absence of any tz database (system files and `tzdata` package).

### Changed
- **`tzdata` is now a runtime dependency.** Consumers that added `tzdata` themselves to work around the decode failure (e.g. pipelex) can drop it once they bump their kajson pin.
- **`"UTC"` decodes to `datetime.timezone.utc`** instead of `ZoneInfo("UTC")`. The instant and offset are identical; only the tzinfo object type changes.

### Security
- **Refreshed dev/docs lockfile pins to clear all open Dependabot alerts** (urllib3, idna, pymdown-extensions, pytest, Pygments). None of these affected kajson's runtime surface — the package's only runtime dependencies are `pydantic` and `tzdata`; the flagged packages come in through the `dev` and `docs` extras.

## [v0.6.0] - 2026-05-29

### Added
- **Pydantic dataclass decoding:** `UniversalJSONDecoder` now reconstructs pydantic dataclasses through their pydantic validator. Previously a pydantic dataclass only survived deserialization via the untested generic constructor catch-all, and a malformed payload silently fell through to a raw `dict`. The decoder now has an explicit pydantic-dataclass branch (after the `Enum` / `BaseModel` branches) that validates the payload and raises `KajsonDecoderError` loudly on any validation or construction failure (including exceptions raised by a dataclass `__post_init__`, which pydantic does not wrap into a `ValidationError`). Nested `BaseModel` fields, `Optional` fields, lists of pydantic dataclasses, `timedelta` fields, `@pydantic_dataclass(slots=True)` instances, and subclass type preservation all round-trip correctly. Known limitations: (1) a `field(init=False)` attribute set imperatively to a value that diverges from its default is not preserved across a round-trip, because decoding reconstructs through the constructor and pydantic silently ignores `init=False` kwargs; (2) a field declared with `Field(alias=...)` does not round-trip — the encoder writes the Python field name while the constructor expects the alias unless `populate_by_name=True`; the same gap exists for `BaseModel` instances and will be addressed by a future release that aligns the encoder and decoder for both paths.
- **`dataclasses.fields()` encoder fallback:** The universal encoder now falls back to `dataclasses.fields()` when an object exposes no `__dict__` (e.g. slots dataclasses), so slotted dataclasses serialize via their declared fields instead of failing as "not JSON serializable".

### Security
- **Decoder error messages no longer include the raw payload.** Validation failures for `BaseModel`, `RootModel`, `Enum`, and pydantic dataclasses previously embedded the full `the_dict` (and the constructed `base_model_obj` / `root_model_obj`) in both the raised `KajsonDecoderError` and the debug log, which could leak secret-bearing sibling fields (passwords, tokens, API keys) when a single field failed validation. The chained pydantic `ValidationError` (accessible via `__cause__`) still carries the specific offending value for debugging.

## [v0.5.0] - 2026-05-04

### Added
- **`ClassRegistryAbstract.get_classes_dict()`:** New abstract method (with implementation in `ClassRegistry`) that returns a snapshot dict of all registered classes by name. The returned dict is a copy, so mutations do not affect the registry. Useful for pre-seeding a scoped registry from another one.

### Changed
- **Breaking:** Subclasses of `ClassRegistryAbstract` must now implement `get_classes_dict()`.

## [v0.4.2] - 2026-04-02

### Fixed
- **Global Registry Fallback:** When a class's `__module__` points to a loaded module (e.g. `builtins`) but the class isn't found in it, the decoder now falls through to the global `KajsonManager` registry before raising an error. Previously this raised immediately, causing deserialization failures for `exec()`-generated classes registered only in the global registry.

## [v0.4.1] - 2026-04-02

### Added
 - **Class Source Code Support:** Added a `class_source_code` parameter to `kajson.loads()` and `kajson.load()`, enabling deserialization of BaseModel subclasses defined in raw Python source code. The source is exec'd and discovered classes are registered automatically. When combined with an explicit `class_registry`, the registry takes priority.

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
