# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from zoneinfo import ZoneInfo

from kajson import kajson


class TestTimezoneEncoder:
    """Test cases for timezone encoding functions."""

    def test_json_encode_timezone(self) -> None:
        """Test json_encode_timezone function (covers line 95)."""
        timezone = ZoneInfo("America/New_York")
        result = kajson.json_encode_timezone(timezone)

        expected = {"zone": "America/New_York", "__class__": "timezone", "__module__": "zoneinfo"}
        assert result == expected

    def test_json_encode_timezone_utc(self) -> None:
        """Test json_encode_timezone with UTC timezone."""
        timezone = ZoneInfo("UTC")
        result = kajson.json_encode_timezone(timezone)

        expected = {"zone": "UTC", "__class__": "timezone", "__module__": "zoneinfo"}
        assert result == expected
