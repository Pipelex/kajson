# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import datetime
from typing import Any

import pytest

from kajson import kajson
from kajson.exceptions import KajsonDecoderError


class TestTimedeltaEncoder:
    """Test cases for timedelta encoding function."""

    def test_json_encode_timedelta_positive(self) -> None:
        """Test json_encode_timedelta with positive timedelta (covers line 190)."""
        test_timedelta = datetime.timedelta(days=5, hours=3, minutes=30, seconds=45)
        result = kajson.json_encode_timedelta(test_timedelta)

        expected_seconds = test_timedelta.total_seconds()
        expected = {"seconds": expected_seconds}
        assert result == expected

    def test_json_encode_timedelta_negative(self) -> None:
        """Test json_encode_timedelta with negative timedelta."""
        test_timedelta = datetime.timedelta(days=-2, hours=-5)
        result = kajson.json_encode_timedelta(test_timedelta)

        expected_seconds = test_timedelta.total_seconds()
        expected = {"seconds": expected_seconds}
        assert result == expected
        assert result["seconds"] < 0

    def test_json_encode_timedelta_zero(self) -> None:
        """Test json_encode_timedelta with zero timedelta."""
        test_timedelta = datetime.timedelta()
        result = kajson.json_encode_timedelta(test_timedelta)

        expected = {"seconds": 0.0}
        assert result == expected

    def test_json_encode_timedelta_microseconds(self) -> None:
        """Test json_encode_timedelta with microseconds."""
        test_timedelta = datetime.timedelta(seconds=1, microseconds=500000)
        result = kajson.json_encode_timedelta(test_timedelta)

        expected = {"seconds": 1.5}
        assert result == expected

    def test_timedelta_roundtrip_serialization(self) -> None:
        """Test complete timedelta serialization roundtrip."""
        original_timedelta = datetime.timedelta(days=3, hours=2, minutes=30, seconds=45, microseconds=123456)

        # Encode
        json_str = kajson.dumps(original_timedelta)

        # Decode (handled by the registered timedelta decoder)
        decoded_timedelta = kajson.loads(json_str)

        assert decoded_timedelta == original_timedelta
        assert isinstance(decoded_timedelta, datetime.timedelta)

    def test_timedelta_decoder_is_registered(self) -> None:
        assert kajson.UniversalJSONDecoder.get_registered_decoder(datetime.timedelta) is kajson.json_decode_timedelta

    @pytest.mark.parametrize(
        ("fields", "expected"),
        [
            ({"seconds": 90.5}, datetime.timedelta(seconds=90.5)),
            ({"days": 2, "hours": 3}, datetime.timedelta(days=2, hours=3)),
            (
                {"weeks": 1, "minutes": -5, "milliseconds": 10, "microseconds": 7},
                datetime.timedelta(weeks=1, minutes=-5, milliseconds=10, microseconds=7),
            ),
            ({}, datetime.timedelta()),
        ],
    )
    @pytest.mark.parametrize("safe", [False, True])
    def test_timedelta_decodes_every_constructor_keyword(self, fields: dict[str, Any], expected: datetime.timedelta, safe: bool) -> None:
        payload = kajson.json.dumps({**fields, "__class__": "timedelta", "__module__": "datetime"})
        assert kajson.loads(payload, safe=safe) == expected

    @pytest.mark.parametrize(
        ("fields", "message"),
        [
            ({"seconds": 1, "evil": 2}, "1 unexpected key"),
            ({"seconds": "10"}, "expected 'seconds' to be a number"),
            ({"seconds": True}, "expected 'seconds' to be a number"),
            ({"days": None}, "expected 'days' to be a number"),
            ({"days": 10**12}, "Could not decode timedelta"),
            ({"seconds": 1e300}, "Could not decode timedelta"),
        ],
    )
    @pytest.mark.parametrize("safe", [False, True])
    def test_malformed_timedelta_payload_raises(self, fields: dict[str, Any], message: str, safe: bool) -> None:
        """A malformed timedelta used to come back silently as a raw dict."""
        payload = kajson.json.dumps({**fields, "__class__": "timedelta", "__module__": "datetime"})
        with pytest.raises(KajsonDecoderError, match=message):
            kajson.loads(payload, safe=safe)
