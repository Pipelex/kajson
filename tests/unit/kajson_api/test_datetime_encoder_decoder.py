# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import datetime
from zoneinfo import ZoneInfo

import pytest

from kajson import kajson
from kajson.exceptions import KajsonDecoderError


class TestDatetimeEncoderDecoder:
    """Test cases for datetime encoding and decoding functions."""

    def test_json_encode_datetime_naive(self) -> None:
        """Test json_encode_datetime with naive datetime (covers lines 126-127)."""
        test_datetime = datetime.datetime(2023, 12, 25, 14, 30, 45, 123456)
        result = kajson.json_encode_datetime(test_datetime)

        expected = {"datetime": "2023-12-25 14:30:45.123456", "tzinfo": None, "__class__": "datetime", "__module__": "datetime"}
        assert result == expected

    def test_json_encode_datetime_with_timezone(self) -> None:
        """Test json_encode_datetime with timezone-aware datetime."""
        timezone = ZoneInfo("America/New_York")
        test_datetime = datetime.datetime(2023, 12, 25, 14, 30, 45, 123456, tzinfo=timezone)
        result = kajson.json_encode_datetime(test_datetime)

        expected = {"datetime": "2023-12-25 14:30:45.123456", "tzinfo": "America/New_York", "__class__": "datetime", "__module__": "datetime"}
        assert result == expected

    def test_json_decode_datetime_naive(self) -> None:
        """Test json_decode_datetime with naive datetime."""
        test_dict = {"datetime": "2023-12-25 14:30:45.123456", "tzinfo": None}
        result = kajson.json_decode_datetime(test_dict)

        expected = datetime.datetime(2023, 12, 25, 14, 30, 45, 123456)
        assert result == expected
        assert result.tzinfo is None

    def test_json_decode_datetime_with_timezone(self) -> None:
        """Test json_decode_datetime with timezone."""
        test_dict = {"datetime": "2023-12-25 14:30:45.123456", "tzinfo": "UTC"}
        result = kajson.json_decode_datetime(test_dict)

        expected = datetime.datetime(2023, 12, 25, 14, 30, 45, 123456, tzinfo=ZoneInfo("UTC"))
        assert result == expected
        assert result.tzinfo is not None

    def test_json_decode_datetime_missing_datetime_field(self) -> None:
        """Test json_decode_datetime with missing datetime field (covers line 149)."""
        test_dict = {"tzinfo": "UTC"}

        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.json_decode_datetime(test_dict)

        assert "Could not decode datetime from json: datetime field is required" in str(excinfo.value)

    def test_datetime_roundtrip_serialization(self) -> None:
        """Test complete datetime serialization roundtrip."""
        original_datetime = datetime.datetime(2023, 6, 15, 10, 30, 45, 123456, tzinfo=ZoneInfo("Europe/Paris"))

        # Encode
        json_str = kajson.dumps(original_datetime)

        # Decode
        decoded_datetime = kajson.loads(json_str)

        assert decoded_datetime == original_datetime
        assert isinstance(decoded_datetime, datetime.datetime)
