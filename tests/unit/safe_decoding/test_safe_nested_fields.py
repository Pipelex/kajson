# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Any

import pytest

import kajson
from kajson.exceptions import KajsonDecoderError
from tests.unit.safe_decoding.safe_decoding_classes import (
    InitOverridingModel,
    NewOverridingDataclass,
    NewOverridingModel,
    PointHolder,
    ProbePackages,
    PydanticPoint,
    TreeNode,
    error_chain_text,
    make_marker,
)


@pytest.mark.usefixtures("reset_counters")
class TestSafeNestedFields:
    def test_model_holding_base_settings_is_refused_before_the_env_file_is_read(self, tmp_path: Path) -> None:
        env_file = tmp_path / "secrets.env"
        env_file.write_text("SENTINEL_TOKEN=s3cr3t-sentinel-value\n")
        with pytest.raises(KajsonDecoderError, match="'EnvFileSettings', which overrides __init__") as excinfo:
            kajson.loads(make_marker("HoldsEnvFileSettings", settings={"_env_file": str(env_file)}), safe=True)
        assert "s3cr3t-sentinel-value" not in error_chain_text(excinfo.value)

    @pytest.mark.parametrize(
        ("holder", "fields", "counted", "overridden"),
        [
            ("HoldsInitOverridingModel", {"inner": {"number": 1}}, InitOverridingModel, "overrides __init__"),
            ("HoldsNewOverridingModel", {"inner": {"number": 1}}, NewOverridingModel, "overrides __new__"),
            ("HoldsNewOverridingDataclass", {"inner": {"number": 1}}, NewOverridingDataclass, "overrides __new__"),
            ("DeeplyHoldsInitOverridingModel", {"layers": [{"key": {"inner": {"number": 1}}}]}, InitOverridingModel, "overrides __init__"),
            ("RecursiveHolder", {"children": [], "danger": {"number": 1}}, InitOverridingModel, "overrides __init__"),
        ],
        ids=["nested-init", "nested-new", "nested-dataclass-new", "deeply-nested", "recursive-definitions"],
    )
    def test_model_holding_an_overriding_class_is_refused(self, holder: str, fields: dict[str, Any], counted: Any, overridden: str) -> None:
        with pytest.raises(KajsonDecoderError, match=overridden):
            kajson.loads(make_marker(holder, **fields), safe=True)
        assert counted.calls == 0

    def test_import_string_field_is_refused_and_imports_nothing(self, probes: ProbePackages) -> None:
        probes.write("evil")
        with pytest.raises(KajsonDecoderError, match="ImportString"):
            kajson.loads(make_marker("ImportStringModel", target=probes.full("evil")), safe=True)
        assert not probes.was_imported("evil")

    def test_import_string_field_still_imports_in_permissive_mode(self, probes: ProbePackages) -> None:
        """Pins what the refusal prevents: validating the field imports the module its value names."""
        probes.write("evil")
        kajson.loads(make_marker("ImportStringModel", target=probes.full("evil")))
        assert probes.was_imported("evil")

    @pytest.mark.parametrize(
        "value",
        [
            TreeNode(name="root", children=[TreeNode(name="leaf", children=[])]),
            PointHolder(point=PydanticPoint(abscissa=1, ordinate=2)),
        ],
        ids=["recursive-model", "dataclass-holding-dataclass"],
    )
    def test_nested_pydantic_classes_of_the_library_round_trip(self, value: Any) -> None:
        assert kajson.loads(kajson.dumps(value), safe=True) == value
