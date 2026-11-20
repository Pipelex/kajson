# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

import kajson
from kajson.exceptions import KajsonDecoderError
from tests.unit.safe_decoding.safe_decoding_classes import make_marker


class TestSafeRebuild:
    @pytest.mark.usefixtures("registered_decoders")
    def test_failing_registered_decoder_raises_even_with_fallback_enabled(self, mocker: MockerFixture) -> None:
        mocker.patch("kajson.json_decoder.IS_DECODER_FALLBACK_ENABLED", True)
        with pytest.raises(KajsonDecoderError, match="registered decoder failed"):
            kajson.loads(make_marker("WithFailingRegisteredDecoder"), safe=True)

    def test_failing_json_decode_raises_even_with_fallback_enabled(self, mocker: MockerFixture) -> None:
        mocker.patch("kajson.json_decoder.IS_DECODER_FALLBACK_ENABLED", True)
        with pytest.raises(KajsonDecoderError, match="hook failed"):
            kajson.loads(make_marker("WithFailingJsonDecode"), safe=True)

    def test_attribute_error_inside_json_decode_raises(self) -> None:
        with pytest.raises(KajsonDecoderError, match="AttributeError"):
            kajson.loads(make_marker("WithAttributeErrorJsonDecode"), safe=True)

    def test_model_failing_validation_raises_without_the_constructor_fallback(self) -> None:
        with pytest.raises(KajsonDecoderError, match="Could not model_validate") as excinfo:
            kajson.loads(make_marker("ValidatedModel", value=-1), safe=True)
        assert "using kwargs" not in str(excinfo.value)
        assert isinstance(excinfo.value.__cause__, ValidationError)

    def test_permissive_mode_still_falls_back_to_the_constructor(self) -> None:
        """Pins the permissive path that safe mode removes: a failed model_validate is retried through the constructor."""
        with pytest.raises(KajsonDecoderError, match="using kwargs"):
            kajson.loads(make_marker("ValidatedModel", value=-1))

    @pytest.mark.parametrize(
        ("fields", "message"),
        [
            ({}, "'root'"),
            ({"root": [1], "extra": 2}, "'root'"),
            ({"root": "not a list"}, "RootModel"),
        ],
        ids=["missing-root", "extra-key", "invalid-root"],
    )
    def test_malformed_root_model_payload_raises(self, fields: Dict[str, Any], message: str) -> None:
        with pytest.raises(KajsonDecoderError, match=message):
            kajson.loads(make_marker("IntListRoot", **fields), safe=True)

    def test_pydantic_dataclass_failing_validation_raises(self) -> None:
        with pytest.raises(KajsonDecoderError, match="pydantic dataclass"):
            kajson.loads(make_marker("PydanticPoint", abscissa="not an int", ordinate=1), safe=True)

    def test_enum_with_unhashable_name_raises_a_decoder_error(self) -> None:
        with pytest.raises(KajsonDecoderError):
            kajson.loads(make_marker("Color", _name_=["RED"]), safe=True)
