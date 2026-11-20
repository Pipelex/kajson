# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import importlib
import sys
import uuid
from pathlib import Path

import pytest

import kajson
from kajson.exceptions import KajsonDecoderError
from tests.unit.safe_decoding.safe_decoding_classes import PlainModel, ProbePackages, make_marker


class TestSafeImports:
    def test_module_outside_importable_packages_is_not_imported(self, probes: ProbePackages) -> None:
        with pytest.raises(KajsonDecoderError, match="Refusing to import module"):
            kajson.loads(make_marker("ProbeModel", probes.full(""), value=1), safe=True)
        assert probes.full("") not in sys.modules
        assert not probes.was_imported("")

    def test_module_inside_importable_packages_is_imported_and_decodes(self, probes: ProbePackages) -> None:
        result = kajson.loads(make_marker("ProbeModel", probes.full(""), value=7), safe=True, importable_packages=[probes.full("")])
        assert type(result).__name__ == "ProbeModel"
        assert result.value == 7
        assert probes.was_imported("")

    @pytest.mark.parametrize(
        ("allowed", "target", "admitted"),
        [
            ("", "", True),
            ("", "sub", True),
            ("", "sub.leaf", True),
            ("", "evil", False),
            ("sub", "sub", True),
            ("sub", "sub.leaf", True),
            ("sub", "other", False),
        ],
    )
    def test_importable_packages_match_on_package_boundaries(self, probes: ProbePackages, allowed: str, target: str, admitted: bool) -> None:
        payload = make_marker("ProbeModel", probes.full(target), value=1)
        if admitted:
            result = kajson.loads(payload, safe=True, importable_packages=[probes.full(allowed)])
            assert result.value == 1
            assert probes.was_imported(target)
        else:
            with pytest.raises(KajsonDecoderError, match="Refusing to import module"):
                kajson.loads(payload, safe=True, importable_packages=[probes.full(allowed)])
            assert probes.full(target) not in sys.modules
            assert not probes.was_imported(target)

    def test_model_in_an_already_imported_module_outside_the_packages_still_decodes(self) -> None:
        """Pins the documented residual: resolution from sys.modules is not gated by importable_packages."""
        result = kajson.loads(kajson.dumps(PlainModel(name="residual")), safe=True, importable_packages=["some_other_package"])
        assert result == PlainModel(name="residual")

    def test_module_level_getattr_does_not_run_in_safe_mode(self, tmp_path: Path, extra_sys_path: Path) -> None:
        module_name = f"kjlazy_{uuid.uuid4().hex[:12]}"
        record = tmp_path / "getattr-ran"
        (extra_sys_path / f"{module_name}.py").write_text(
            f"import pathlib\n\n\ndef __getattr__(name):\n    pathlib.Path({str(record)!r}).write_text(name)\n    raise AttributeError(name)\n"
        )
        importlib.import_module(module_name)
        with pytest.raises(KajsonDecoderError, match="not found"):
            kajson.loads(make_marker("Lazy", module_name), safe=True)
        assert not record.exists()

    def test_module_level_getattr_still_runs_in_permissive_mode(self, tmp_path: Path, extra_sys_path: Path) -> None:
        module_name = f"kjlazy_{uuid.uuid4().hex[:12]}"
        record = tmp_path / "getattr-ran"
        (extra_sys_path / f"{module_name}.py").write_text(
            f"import pathlib\n\n\ndef __getattr__(name):\n    pathlib.Path({str(record)!r}).write_text(name)\n    raise AttributeError(name)\n"
        )
        importlib.import_module(module_name)
        with pytest.raises(KajsonDecoderError, match="not found"):
            kajson.loads(make_marker("Lazy", module_name))
        assert record.read_text() == "Lazy"
