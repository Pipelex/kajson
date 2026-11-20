# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import io
import json
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

import kajson
from kajson.class_registry import ClassRegistry
from kajson.exceptions import KajsonDecoderError
from kajson.kajson_manager import KajsonManager
from tests.unit.safe_decoding.safe_decoding_classes import (
    MODULE_NAME,
    BaseInitFlaggedModel,
    CountingEnumMeta,
    CountingModelMetaclass,
    InitOverridingModel,
    InitOverridingRoot,
    KeywordConstructorCounter,
    MetaclassCallModel,
    NewOverridingModel,
    NoArgConstructorCounter,
    StdlibDataclass,
    ValidateOverridingModel,
    ValidateOverridingRoot,
    error_chain_text,
    make_marker,
)


def _in_model_field(inner: dict[str, Any]) -> Any:
    return {"__class__": "AnyFieldModel", "__module__": MODULE_NAME, "payload": inner}


def _in_list(inner: dict[str, Any]) -> Any:
    return [1, inner, 3]


def _in_dict_value(inner: dict[str, Any]) -> Any:
    return {"outer": {"key": inner}}


@pytest.mark.usefixtures("reset_counters")
class TestSafeRefusals:
    def test_popen_marker_is_refused_and_the_command_does_not_run(self, tmp_path: Path) -> None:
        target = tmp_path / "popen-ran"
        assert "subprocess" in sys.modules
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.loads(make_marker("Popen", "subprocess", args=["touch", str(target)]), safe=True)
        assert not target.exists()

    def test_popen_marker_still_runs_in_permissive_mode(self, tmp_path: Path) -> None:
        """Pins why safe mode exists: the permissive decoder builds the Popen and runs the command."""
        target = tmp_path / "popen-ran"
        result = kajson.loads(make_marker("Popen", "subprocess", args=["touch", str(target)]))
        assert isinstance(result, subprocess.Popen)
        result.wait()
        assert target.exists()

    def test_file_io_marker_is_refused_and_the_file_keeps_its_contents(self, tmp_path: Path) -> None:
        victim = tmp_path / "victim.txt"
        victim.write_text("precious")
        assert io.FileIO.__name__ == "FileIO"
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.loads(make_marker("FileIO", "io", file=str(victim), mode="w"), safe=True)
        assert victim.read_text() == "precious"

    def test_thread_marker_is_refused(self) -> None:
        assert threading.Thread.__module__ == "threading"
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.loads(make_marker("Thread", "threading", target=None), safe=True)

    @pytest.mark.parametrize("counted", [NoArgConstructorCounter, KeywordConstructorCounter])
    def test_plain_class_constructor_is_never_called(self, counted: Any) -> None:
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.loads(make_marker(counted.__name__, anything=1), safe=True)
        assert counted.calls == 0

    def test_stdlib_dataclass_is_refused_and_the_message_says_what_safe_mode_rebuilds(self) -> None:
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(kajson.dumps(StdlibDataclass(number=1)), safe=True)
        assert "pydantic BaseModel" in str(excinfo.value)
        assert "registered decoder" in str(excinfo.value)

    def test_builtin_type_is_refused(self) -> None:
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.loads(make_marker("type", "builtins"), safe=True)

    def test_plain_class_in_explicit_registry_is_refused(self) -> None:
        registry = ClassRegistry()
        registry.register_class(KeywordConstructorCounter, name="Counter")
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.loads(make_marker("Counter", "nowhere"), class_registry=registry, safe=True)
        assert KeywordConstructorCounter.calls == 0

    def test_plain_class_in_global_registry_is_refused(self) -> None:
        KajsonManager.get_class_registry().register_class(KeywordConstructorCounter, name="GlobalCounter")
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.loads(make_marker("GlobalCounter", "not_imported_kajson_module"), safe=True)
        assert KeywordConstructorCounter.calls == 0
        assert "not_imported_kajson_module" not in sys.modules

    def test_refusal_message_quotes_names_and_omits_values(self) -> None:
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(make_marker("KeywordConstructorCounter", password="hunter2"), safe=True)
        assert f"'{MODULE_NAME}.KeywordConstructorCounter'" in str(excinfo.value)
        assert "hunter2" not in error_chain_text(excinfo.value)

    def test_base_settings_reading_an_env_file_is_refused_without_leaking_it(self, tmp_path: Path) -> None:
        env_file = tmp_path / "secrets.env"
        env_file.write_text("SENTINEL_TOKEN=s3cr3t-sentinel-value\n")
        with pytest.raises(KajsonDecoderError, match="overrides __init__") as excinfo:
            kajson.loads(make_marker("BaseSettings", "pydantic_settings", _env_file=str(env_file)), safe=True)
        assert "s3cr3t-sentinel-value" not in error_chain_text(excinfo.value)

    def test_base_settings_subclass_is_refused_without_leaking_the_file(self, tmp_path: Path) -> None:
        env_file = tmp_path / "secrets.env"
        env_file.write_text("SENTINEL_TOKEN=s3cr3t-sentinel-value\n")
        with pytest.raises(KajsonDecoderError, match="overrides __init__") as excinfo:
            kajson.loads(make_marker("EnvFileSettings", _env_file=str(env_file)), safe=True)
        assert "s3cr3t-sentinel-value" not in error_chain_text(excinfo.value)

    @pytest.mark.parametrize(
        ("model", "counted", "overridden"),
        [
            (InitOverridingModel, InitOverridingModel, "__init__"),
            (BaseInitFlaggedModel, BaseInitFlaggedModel, "__init__"),
            (NewOverridingModel, NewOverridingModel, "__new__"),
            (ValidateOverridingModel, ValidateOverridingModel, "model_validate"),
            (MetaclassCallModel, CountingModelMetaclass, "metaclass __call__"),
        ],
    )
    def test_model_overriding_its_construction_is_refused(self, model: type[BaseModel], counted: Any, overridden: str) -> None:
        with pytest.raises(KajsonDecoderError, match=overridden):
            kajson.loads(make_marker(model.__name__, number=1), safe=True)
        assert counted.calls == 0

    def test_root_model_overriding_init_is_refused(self) -> None:
        with pytest.raises(KajsonDecoderError, match="__init__"):
            kajson.loads(make_marker("InitOverridingRoot", root=1), safe=True)
        assert InitOverridingRoot.calls == 0

    def test_root_model_overriding_model_validate_is_refused(self) -> None:
        with pytest.raises(KajsonDecoderError, match="model_validate"):
            kajson.loads(make_marker("ValidateOverridingRoot", root=1), safe=True)
        assert ValidateOverridingRoot.calls == 0

    @pytest.mark.parametrize(
        "marker",
        [
            make_marker("A" * 10_000, "not_imported_kajson_module"),
            make_marker("B" * 10_000, MODULE_NAME),
            make_marker("Color[" + "C" * 10_000 + "]", _name_="NOPE"),
            make_marker("WithFailingJsonDecode[" + "D" * 10_000 + "]"),
            make_marker("PlainModel", "E" * 10_000),
        ],
        ids=["refused-import", "not-found", "enum-error", "hook-error", "long-module"],
    )
    def test_every_message_cuts_a_very_long_name(self, marker: str) -> None:
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(marker, safe=True)
        assert len(str(excinfo.value)) < 1_000

    def test_enum_whose_metaclass_overrides_call_is_refused(self) -> None:
        with pytest.raises(KajsonDecoderError, match="metaclass __call__"):
            kajson.loads(make_marker("MetaclassCallEnum", _value_=1), safe=True)
        assert CountingEnumMeta.calls == 0

    @pytest.mark.parametrize("wrap", [_in_model_field, _in_list, _in_dict_value])
    def test_refused_marker_nested_anywhere_fails_the_whole_decode(self, wrap: Callable[[dict[str, Any]], Any]) -> None:
        inner = {"__class__": "KeywordConstructorCounter", "__module__": MODULE_NAME, "number": 1}
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.loads(json.dumps(wrap(inner)), safe=True)
        assert KeywordConstructorCounter.calls == 0
