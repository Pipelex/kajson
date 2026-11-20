# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import pytest

import kajson
from kajson.exceptions import KajsonDecoderError
from tests.unit.safe_decoding.safe_decoding_classes import make_marker

SECRET = "hunter2-sentinel"


class TestSafeMessages:
    @pytest.mark.parametrize(
        ("marker", "expected"),
        [
            (make_marker("ValidatedModel", value=SECRET), "'value': Input should be a valid integer"),
            (make_marker("IntListRoot", root=[SECRET]), "'0': Input should be a valid integer"),
            (make_marker("PydanticPoint", abscissa=SECRET, ordinate=1), "'abscissa': Input should be a valid integer"),
            (make_marker("Color", _name_=SECRET), "no member has that name"),
            (make_marker("Color", _value_=SECRET), "no member has that value"),
            (make_marker("RuntimeErrorValidatorModel", value=SECRET), "RuntimeError"),
            (make_marker("timedelta", "datetime", days=1, **{SECRET: 1}), "1 unexpected key"),
        ],
        ids=["model", "root-model", "pydantic-dataclass", "enum-name", "enum-value", "unwrapped-validator-error", "timedelta-key"],
    )
    def test_message_describes_the_failure_without_the_payload_value(self, marker: str, expected: str) -> None:
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(marker, safe=True)
        assert expected in str(excinfo.value)
        assert SECRET not in str(excinfo.value)

    def test_timedelta_overflow_message_leaves_the_value_out(self) -> None:
        with pytest.raises(KajsonDecoderError, match="out of range") as excinfo:
            kajson.loads(make_marker("timedelta", "datetime", days=123456789123), safe=True)
        assert "123456789123" not in str(excinfo.value)

    def test_original_error_stays_chained_for_debugging(self) -> None:
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(make_marker("ValidatedModel", value=SECRET), safe=True)
        assert SECRET in str(excinfo.value.__cause__)
