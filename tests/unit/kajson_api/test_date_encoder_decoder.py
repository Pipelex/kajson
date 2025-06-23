# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import datetime

from kajson import kajson


class TestDateEncoderDecoder:
    """Test cases for date encoding and decoding functions."""

    def test_json_encode_date(self) -> None:
        """Test json_encode_date function."""
        test_date = datetime.date(2023, 12, 25)
        result = kajson.json_encode_date(test_date)

        expected = {"date": "2023-12-25"}
        assert result == expected

    def test_json_decode_date(self) -> None:
        """Test json_decode_date function (covers line 111)."""
        test_dict = {"date": "2023-12-25"}
        result = kajson.json_decode_date(test_dict)

        expected = datetime.date(2023, 12, 25)
        assert result == expected

    def test_json_decode_date_leap_year(self) -> None:
        """Test json_decode_date with leap year date (covers line 117)."""
        test_dict = {"date": "2024-02-29"}
        result = kajson.json_decode_date(test_dict)

        expected = datetime.date(2024, 2, 29)
        assert result == expected

    def test_date_roundtrip_serialization(self) -> None:
        """Test complete date serialization roundtrip."""
        original_date = datetime.date(2023, 6, 15)

        # Encode
        json_str = kajson.dumps(original_date)

        # Decode
        decoded_date = kajson.loads(json_str)

        assert decoded_date == original_date
        assert isinstance(decoded_date, datetime.date)
