# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import io
import json
from pathlib import Path

import pytest

import kajson
from kajson.class_registry import ClassRegistry
from kajson.exceptions import KajsonDecoderError
from kajson.json_decoder import UniversalJSONDecoder
from tests.unit.safe_decoding.safe_decoding_classes import KeywordConstructorCounter, PlainModel, ResolvingSubclass, make_marker


class TestSafeEntryPoints:
    def test_load_refuses_the_popen_marker_from_a_file(self, tmp_path: Path) -> None:
        target = tmp_path / "popen-ran"
        stream = io.StringIO(make_marker("Popen", "subprocess", args=["touch", str(target)]))
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            kajson.load(stream, safe=True)
        assert not target.exists()

    def test_json_loads_with_the_decoder_class_refuses_the_popen_marker(self, tmp_path: Path) -> None:
        target = tmp_path / "popen-ran"
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            json.loads(make_marker("Popen", "subprocess", args=["touch", str(target)]), cls=UniversalJSONDecoder, safe=True)
        assert not target.exists()

    @pytest.mark.parametrize("safe", [True, False])
    def test_stdlib_strict_still_reaches_the_json_decoder(self, safe: bool) -> None:
        with_control_character = '{"text": "line\tbreak"}'
        assert kajson.loads(with_control_character, safe=safe, strict=False) == {"text": "line\tbreak"}
        with pytest.raises(json.JSONDecodeError):
            kajson.loads(with_control_character, safe=safe)

    def test_subclass_calling_apply_decoder_strategies_still_decodes(self) -> None:
        """Stands for pipelex-server's RestrictedPayloadDecoder until it is replaced by safe=True."""
        registry = ClassRegistry()
        registry.register_class(PlainModel)
        result = json.loads(kajson.dumps(PlainModel(name="sub")), cls=ResolvingSubclass, class_registry=registry)
        assert result == PlainModel(name="sub")

    @pytest.mark.usefixtures("reset_counters")
    def test_subclass_calling_the_rebuild_keeps_safe_mode(self) -> None:
        """A subclass that replaces resolution and calls _apply_decoder_strategies still refuses in safe mode."""
        registry = ClassRegistry()
        registry.register_class(KeywordConstructorCounter)
        with pytest.raises(KajsonDecoderError, match="Refusing to instantiate"):
            json.loads(make_marker("KeywordConstructorCounter", number=1), cls=ResolvingSubclass, class_registry=registry, safe=True)
        assert KeywordConstructorCounter.calls == 0
