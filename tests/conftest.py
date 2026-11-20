import importlib
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

import kajson.kajson_manager
from kajson.json_decoder import UniversalJSONDecoder
from tests.unit.safe_decoding.safe_decoding_classes import (
    COUNTED_CLASSES,
    ProbePackages,
    WithFailingRegisteredDecoder,
    WithRegisteredDecoder,
    decode_with_registered,
    failing_registered_decoder,
)


@pytest.fixture(scope="function", autouse=True)
def reset_kajson_manager_fixture():
    # Code to run before each test
    print("\n[magenta]Kajson setup[/magenta]")
    # Ensure clean state before creating instance
    kajson.kajson_manager.KajsonManager.teardown()
    try:
        kajson.kajson_manager.KajsonManager()
    except Exception as exc:
        pytest.exit(f"Critical Kajson setup error: {exc}")
    yield
    # Code to run after each test
    print("\n[magenta]Kajson teardown[/magenta]")
    kajson.kajson_manager.KajsonManager.teardown()


@pytest.fixture
def reset_counters() -> None:
    """Zero the call counters of the safe-decoding test classes."""
    for counted in COUNTED_CLASSES:
        counted.calls = 0


@pytest.fixture
def registered_decoders() -> Generator[None, None, None]:
    """Register decoders for the test classes, and remove them afterwards."""
    UniversalJSONDecoder.register(WithRegisteredDecoder, decode_with_registered)
    UniversalJSONDecoder.register(WithFailingRegisteredDecoder, failing_registered_decoder)
    yield
    UniversalJSONDecoder._decoders.pop(WithRegisteredDecoder, None)  # pyright: ignore[reportPrivateUsage]
    UniversalJSONDecoder._decoders.pop(WithFailingRegisteredDecoder, None)  # pyright: ignore[reportPrivateUsage]


@pytest.fixture
def extra_sys_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Path, None, None]:
    """A directory put first on sys.path for the test; modules imported from it are forgotten afterwards."""
    root = tmp_path / "site"
    root.mkdir()
    monkeypatch.setattr(sys, "path", [str(root), *sys.path])
    importlib.invalidate_caches()
    yield root
    for name, module in list(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if module_file is not None and str(module_file).startswith(str(root)):
            del sys.modules[name]


@pytest.fixture
def probes(tmp_path: Path, extra_sys_path: Path) -> ProbePackages:
    record_dir = tmp_path / "records"
    record_dir.mkdir()
    packages = ProbePackages(extra_sys_path, record_dir)
    for module in ("", "sub", "sub.leaf", "other", "evil"):
        packages.write(module)
    return packages
