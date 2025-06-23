# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import datetime

from kajson import kajson


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

        # Decode (should be handled by automatic constructor calling)
        decoded_timedelta = kajson.loads(json_str)

        assert decoded_timedelta == original_timedelta
        assert isinstance(decoded_timedelta, datetime.timedelta)
