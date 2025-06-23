# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import datetime
from zoneinfo import ZoneInfo

from kajson import kajson


class TestTimeEncoderDecoder:
    """Test cases for time encoding and decoding functions."""

    def test_json_encode_time_naive(self) -> None:
        """Test json_encode_time with naive time (covers line 152)."""
        test_time = datetime.time(14, 30, 45, 123456)
        result = kajson.json_encode_time(test_time)

        expected = {"time": "14:30:45.123456", "tzinfo": None}
        assert result == expected

    def test_json_encode_time_with_timezone(self) -> None:
        """Test json_encode_time with timezone-aware time."""
        timezone = ZoneInfo("America/New_York")
        test_time = datetime.time(14, 30, 45, 123456, tzinfo=timezone)
        result = kajson.json_encode_time(test_time)

        expected = {"time": "14:30:45.123456", "tzinfo": timezone}
        assert result == expected

    def test_json_decode_time_naive(self) -> None:
        """Test json_decode_time with naive time (covers lines 163, 172-180)."""
        test_dict = {"time": "14:30:45.123456", "tzinfo": None}
        result = kajson.json_decode_time(test_dict)

        expected = datetime.time(14, 30, 45, 123456)
        assert result == expected
        assert result.tzinfo is None

    def test_json_decode_time_with_timezone(self) -> None:
        """Test json_decode_time with timezone."""
        timezone = ZoneInfo("UTC")
        test_dict = {"time": "14:30:45.123456", "tzinfo": timezone}
        result = kajson.json_decode_time(test_dict)

        expected = datetime.time(14, 30, 45, 123456, tzinfo=timezone)
        assert result == expected
        assert result.tzinfo is timezone

    def test_json_decode_time_zero_microseconds(self) -> None:
        """Test json_decode_time with zero microseconds."""
        test_dict = {"time": "14:30:45.000000", "tzinfo": None}
        result = kajson.json_decode_time(test_dict)

        expected = datetime.time(14, 30, 45, 0)
        assert result == expected

    def test_json_decode_time_no_microseconds(self) -> None:
        """Test json_decode_time parsing different time formats."""
        # Test with small microseconds value
        test_dict = {"time": "09:15:30.000001", "tzinfo": None}
        result = kajson.json_decode_time(test_dict)

        expected = datetime.time(9, 15, 30, 1)
        assert result == expected

    def test_time_roundtrip_serialization(self) -> None:
        """Test complete time serialization roundtrip."""
        original_time = datetime.time(10, 30, 45, 123456)

        # Encode
        json_str = kajson.dumps(original_time)

        # Decode
        decoded_time = kajson.loads(json_str)

        assert decoded_time == original_time
        assert isinstance(decoded_time, datetime.time)
