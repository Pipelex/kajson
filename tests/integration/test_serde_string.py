# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for kajson's string-based serialization (dumps) and deserialization (loads).

These tests exercise round-tripping of various object graphs through
`kajson.dumps` → JSON string → `kajson.loads` and ensure the result is
identical to the original object.

The test cases are provided in :pydata:`tests.test_data.SerDeTestCases` to
cover a representative set of scenarios:

* Pydantic models with nested subclasses and tricky types
* Arbitrary (non-pydantic) types implementing the custom encode/decode hooks
* Heterogeneous lists containing the above objects
* Built-in datetime and timezone types (date, datetime, time, timedelta, ZoneInfo)
* Validation errors raised at decode time

Only integration scenarios that are presently required are covered here. New
cases should be added to *tests/test_data.py* and referenced from this file
when needed.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict
from zoneinfo import ZoneInfo

import pytest
from pydantic import BaseModel

from kajson import kajson
from kajson.exceptions import KajsonDecoderError
from tests.test_data import (
    SerDeTestCases,
    obj_pydantic_tricky_types_json_str4_with_validation_error,
)


class TestKajsonStringSerDe:
    """Collection of kajson round-trip integration tests using JSON strings."""

    # ---------------------------------------------------------------------
    # Pydantic models ------------------------------------------------------
    # ---------------------------------------------------------------------

    @pytest.mark.parametrize("test_obj", SerDeTestCases.PYDANTIC_EXAMPLES)
    def test_roundtrip_pydantic_examples(self, test_obj: Any) -> None:
        """Round-trip a set of representative Pydantic examples."""
        serialized = kajson.dumps(test_obj, indent=4)
        logging.info("Serialized JSON: %s", serialized)

        deserialized = kajson.loads(serialized)
        logging.info("Deserialized object (%s): %s", type(deserialized).__name__, deserialized)

        assert test_obj == deserialized

    @pytest.mark.parametrize(
        "test_obj, _test_obj_dict, _test_obj_dict_typed, test_obj_json_str4",
        SerDeTestCases.PYDANTIC_FULL_CHECKS,
    )
    def test_roundtrip_pydantic_full(
        self,
        test_obj: BaseModel,
        _test_obj_dict: Dict[str, Any],
        _test_obj_dict_typed: Dict[str, Any],
        test_obj_json_str4: str,
    ) -> None:
        """Full round-trip on tricky Pydantic model including string equality.

        This test ensures that:

        1. `kajson.dumps` produces the exact expected pretty-printed JSON
           representation (``test_obj_json_str4``).
        2. `kajson.loads` recreates an object that compares equal to the
           original model.
        """
        serialized = kajson.dumps(test_obj, indent=4)
        logging.info("Serialized JSON: %s", serialized)
        assert serialized == test_obj_json_str4

        deserialized = kajson.loads(serialized)
        logging.info("Deserialized object (%s): %s", type(deserialized).__name__, deserialized)
        assert test_obj == deserialized

    # ------------------------------------------------------------------
    # Validation errors -------------------------------------------------
    # ------------------------------------------------------------------

    def test_validation_error_on_decode(self) -> None:
        """Ensure kajson surfaces validation errors from nested Pydantic models."""
        with pytest.raises(KajsonDecoderError) as excinfo:
            _ = kajson.loads(obj_pydantic_tricky_types_json_str4_with_validation_error)
        expected_substring = "Could not instantiate pydantic BaseModel '<class 'tests.test_data.Number'>' using kwargs: 1 validation error for Number"
        assert expected_substring in str(excinfo.value)

    # ------------------------------------------------------------------
    # Arbitrary objects --------------------------------------------------
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("test_obj", SerDeTestCases.ARBITRARY_TYPES)
    def test_roundtrip_arbitrary_types(self, test_obj: Any) -> None:
        """Round-trip arbitrary (non-pydantic) objects implementing hooks."""
        serialized = kajson.dumps(test_obj, indent=4)
        logging.info("Serialized JSON: %s", serialized)

        deserialized = kajson.loads(serialized)
        logging.info("Deserialized object (%s): %s", type(deserialized).__name__, deserialized)
        assert test_obj == deserialized

    # ------------------------------------------------------------------
    # Lists of mixed objects --------------------------------------------
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("test_obj", SerDeTestCases.LISTS)
    def test_roundtrip_mixed_lists(self, test_obj: Any) -> None:
        """Round-trip lists containing heterogeneous serialisable objects."""
        serialized = kajson.dumps(test_obj, indent=4)
        logging.info("Serialized JSON: %s", serialized)

        deserialized = kajson.loads(serialized)
        logging.info("Deserialized object (%s): %s", type(deserialized).__name__, deserialized)
        assert test_obj == deserialized


class TestDatetimeTimezoneRoundtrip:
    """Integration tests for datetime and timezone serialization round-trips."""

    def test_roundtrip_naive_datetime(self) -> None:
        """Test round-trip serialization of naive datetime objects."""
        original = datetime.datetime(2023, 12, 25, 14, 30, 45, 123456)

        json_str = kajson.dumps(original)
        restored = kajson.loads(json_str)

        assert restored == original
        assert isinstance(restored, datetime.datetime)
        assert restored.tzinfo is None

    def test_roundtrip_timezone_aware_datetime(self) -> None:
        """Test round-trip serialization of timezone-aware datetime objects."""
        original = datetime.datetime(2023, 12, 25, 14, 30, 45, 123456, tzinfo=ZoneInfo("America/New_York"))

        json_str = kajson.dumps(original)
        restored = kajson.loads(json_str)

        assert restored == original
        assert isinstance(restored, datetime.datetime)
        assert restored.tzinfo == ZoneInfo("America/New_York")

    def test_roundtrip_date(self) -> None:
        """Test round-trip serialization of date objects."""
        original = datetime.date(2023, 12, 25)

        json_str = kajson.dumps(original)
        restored = kajson.loads(json_str)

        assert restored == original
        assert isinstance(restored, datetime.date)

    def test_roundtrip_naive_time(self) -> None:
        """Test round-trip serialization of naive time objects."""
        original = datetime.time(14, 30, 45, 123456)

        json_str = kajson.dumps(original)
        restored = kajson.loads(json_str)

        assert restored == original
        assert isinstance(restored, datetime.time)
        assert restored.tzinfo is None

    def test_roundtrip_timezone_aware_time(self) -> None:
        """Test round-trip serialization of timezone-aware time objects."""
        original = datetime.time(14, 30, 45, 123456, tzinfo=ZoneInfo("Europe/London"))

        json_str = kajson.dumps(original)
        restored = kajson.loads(json_str)

        assert restored == original
        assert isinstance(restored, datetime.time)
        assert restored.tzinfo == ZoneInfo("Europe/London")

    def test_roundtrip_timedelta(self) -> None:
        """Test round-trip serialization of timedelta objects."""
        original = datetime.timedelta(days=5, hours=3, minutes=30, seconds=45, microseconds=123456)

        json_str = kajson.dumps(original)
        restored = kajson.loads(json_str)

        assert restored == original
        assert isinstance(restored, datetime.timedelta)

    def test_roundtrip_timezone(self) -> None:
        """Test round-trip serialization of ZoneInfo timezone objects."""
        original = ZoneInfo("UTC")

        json_str = kajson.dumps(original)
        restored = kajson.loads(json_str)

        assert restored == original
        assert isinstance(restored, ZoneInfo)

    @pytest.mark.parametrize("timezone_name", ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo", "Australia/Sydney"])
    def test_roundtrip_various_timezones(self, timezone_name: str) -> None:
        """Test round-trip serialization of various timezone objects."""
        original = ZoneInfo(timezone_name)

        json_str = kajson.dumps(original)
        restored = kajson.loads(json_str)

        assert restored == original
        assert isinstance(restored, ZoneInfo)
        assert str(restored) == timezone_name

    def test_roundtrip_complex_datetime_structure(self) -> None:
        """Test round-trip serialization of complex structure with mixed datetime types."""
        original: dict[str, Any] = {
            "start_date": datetime.date(2023, 1, 1),
            "end_date": datetime.date(2023, 12, 31),
            "start_datetime": datetime.datetime(2023, 1, 1, 9, 0, 0, tzinfo=ZoneInfo("America/New_York")),
            "end_datetime": datetime.datetime(2023, 12, 31, 17, 0, 0, tzinfo=ZoneInfo("America/New_York")),
            "meeting_time": datetime.time(14, 30, tzinfo=ZoneInfo("UTC")),
            "duration": datetime.timedelta(hours=2, minutes=30),
            "timezone": ZoneInfo("America/New_York"),
            "events": [
                {
                    "name": "Event 1",
                    "timestamp": datetime.datetime(2023, 6, 15, 10, 0, 0, tzinfo=ZoneInfo("UTC")),
                    "duration": datetime.timedelta(minutes=45),
                },
                {
                    "name": "Event 2",
                    "timestamp": datetime.datetime(2023, 6, 15, 15, 30, 0, tzinfo=ZoneInfo("Europe/London")),
                    "duration": datetime.timedelta(hours=1, minutes=30),
                },
            ],
        }

        json_str = kajson.dumps(original, indent=2)
        restored = kajson.loads(json_str)

        # Test top-level fields
        assert restored["start_date"] == original["start_date"]
        assert restored["end_date"] == original["end_date"]
        assert restored["start_datetime"] == original["start_datetime"]
        assert restored["end_datetime"] == original["end_datetime"]
        assert restored["meeting_time"] == original["meeting_time"]
        assert restored["duration"] == original["duration"]
        assert restored["timezone"] == original["timezone"]

        # Test nested events
        assert len(restored["events"]) == 2
        for i, event in enumerate(restored["events"]):
            assert event["name"] == original["events"][i]["name"]
            assert event["timestamp"] == original["events"][i]["timestamp"]
            assert event["duration"] == original["events"][i]["duration"]
            assert isinstance(event["timestamp"], datetime.datetime)
            assert isinstance(event["duration"], datetime.timedelta)

        # Verify types are preserved
        assert isinstance(restored["start_date"], datetime.date)
        assert isinstance(restored["start_datetime"], datetime.datetime)
        assert isinstance(restored["meeting_time"], datetime.time)
        assert isinstance(restored["duration"], datetime.timedelta)
        assert isinstance(restored["timezone"], ZoneInfo)

    def test_datetime_edge_cases(self) -> None:
        """Test edge cases for datetime serialization."""
        # Test minimum datetime
        min_dt = datetime.datetime.min
        json_str = kajson.dumps(min_dt)
        restored = kajson.loads(json_str)
        assert restored == min_dt

        # Test maximum datetime
        max_dt = datetime.datetime.max
        json_str = kajson.dumps(max_dt)
        restored = kajson.loads(json_str)
        assert restored == max_dt

        # Test zero timedelta
        zero_td = datetime.timedelta(0)
        json_str = kajson.dumps(zero_td)
        restored = kajson.loads(json_str)
        assert restored == zero_td

        # Test negative timedelta
        neg_td = datetime.timedelta(days=-5, hours=-3)
        json_str = kajson.dumps(neg_td)
        restored = kajson.loads(json_str)
        assert restored == neg_td

    def test_automatic_metadata_addition(self) -> None:
        """Test that automatic metadata (__class__, __module__) is correctly added."""
        original = datetime.datetime(2023, 1, 1, 12, 0, 0)
        json_str = kajson.dumps(original, indent=2)

        # Verify the JSON contains the expected metadata
        assert '"__class__": "datetime"' in json_str
        assert '"__module__": "datetime"' in json_str

        # Verify round-trip still works
        restored = kajson.loads(json_str)
        assert restored == original
        assert isinstance(restored, datetime.datetime)
