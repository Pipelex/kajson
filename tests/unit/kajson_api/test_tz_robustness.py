# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import datetime
from zoneinfo import ZoneInfo

import pytest

from kajson import kajson
from kajson.exceptions import KajsonDecoderError

# Created at import time, while the tz database is still visible. Under the
# no_tz_database fixture this object keeps working (its data is in memory),
# mirroring a payload encoded on a host that had the zone.
PARIS = ZoneInfo("Europe/Paris")


class TestTzRobustness:
    """Round-trip guarantees for aware datetimes/times across tz-database availability.

    Covers the three failure modes behind the pipelex 2026-06-10 incident:
    1. Decoding kajson's own UTC output must not require an external tz database.
    2. Fixed-offset timezones (datetime.timezone) must round-trip at all.
    3. datetime.time must encode/decode consistently for every tzinfo flavor.
    """

    # ------------------------------------------------------------------
    # Failure mode 1: tz-database-less host
    # ------------------------------------------------------------------

    @pytest.mark.usefixtures("no_tz_database")
    def test_utc_datetime_round_trip_without_tz_database(self) -> None:
        """kajson must read back its own UTC output with zero tz-database dependence."""
        original = datetime.datetime(2026, 6, 10, 12, 0, 0, 0, tzinfo=datetime.timezone.utc)
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert decoded.utcoffset() == datetime.timedelta(0)

    @pytest.mark.usefixtures("no_tz_database")
    def test_named_zone_datetime_degrades_to_fixed_offset_without_tz_database(self) -> None:
        """A named zone encoded elsewhere must still decode here, degrading to a fixed offset."""
        original = datetime.datetime(2026, 6, 10, 12, 0, 0, 0, tzinfo=PARIS)
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original  # same instant
        assert decoded.utcoffset() == original.utcoffset()
        # The zone name rides along on the fixed-offset fallback, so re-encoding
        # keeps the zone identity for a later decode on a host with a tz database.
        assert decoded.tzname() == "Europe/Paris"

    @pytest.mark.usefixtures("no_tz_database")
    def test_legacy_named_zone_payload_without_tz_database_raises_helpful_error(self) -> None:
        """Legacy payloads carry no offset: unresolvable names must fail loudly, pointing at tzdata."""
        legacy_payload = '{"datetime": "2026-06-10 12:00:00.000000", "tzinfo": "Europe/Paris", "__class__": "datetime", "__module__": "datetime"}'
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(legacy_payload)
        assert "tzdata" in str(excinfo.value)

    # ------------------------------------------------------------------
    # Failure mode 2: fixed-offset timezones (environment-independent)
    # ------------------------------------------------------------------

    def test_fixed_offset_datetime_round_trip(self) -> None:
        """str(timezone(...)) is not an IANA key; the wire format must not depend on it."""
        original = datetime.datetime.fromisoformat("2026-06-10T12:00:00+02:00")
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert decoded.utcoffset() == datetime.timedelta(hours=2)

    def test_negative_and_subhour_offset_datetime_round_trip(self) -> None:
        original = datetime.datetime(2026, 6, 10, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-5, minutes=-30)))
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert decoded.utcoffset() == datetime.timedelta(hours=-5, minutes=-30)

    def test_custom_named_fixed_offset_datetime_round_trip(self) -> None:
        """timezone(td, 'CEST') stringifies to 'CEST'; both the instant and the name must survive."""
        original = datetime.datetime(2026, 6, 10, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2), "CEST"))
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert decoded.utcoffset() == datetime.timedelta(hours=2)
        assert decoded.tzname() == "CEST"

    def test_utc_named_nonzero_offset_round_trip(self) -> None:
        """A custom tzinfo name colliding with 'UTC' must not silently decode to UTC+0: the offset wins."""
        original = datetime.datetime(2026, 6, 10, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2), "UTC"))
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert decoded.utcoffset() == datetime.timedelta(hours=2)

    def test_named_zone_datetime_round_trip_preserves_zoneinfo(self) -> None:
        """Regression guard: with a tz database present, named zones stay named (DST-aware)."""
        original = datetime.datetime(2023, 6, 15, 10, 30, 45, 123456, tzinfo=PARIS)
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert isinstance(decoded.tzinfo, ZoneInfo)
        assert decoded.tzinfo.key == "Europe/Paris"

    # ------------------------------------------------------------------
    # Failure mode 3: datetime.time codec consistency
    # ------------------------------------------------------------------

    def test_time_naive_round_trip(self) -> None:
        original = datetime.time(14, 30, 45, 123456)
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert decoded.tzinfo is None

    def test_time_with_utc_round_trip(self) -> None:
        """A time at UTC must be serializable at all (encode used to raise TypeError)."""
        original = datetime.time(14, 30, 45, 123456, tzinfo=datetime.timezone.utc)
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original

    def test_time_with_fixed_offset_round_trip(self) -> None:
        original = datetime.time(14, 30, 45, 123456, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original

    def test_time_with_custom_named_fixed_offset_round_trip(self) -> None:
        """A custom name on a time's fixed-offset tzinfo must survive the round trip."""
        original = datetime.time(14, 30, 45, 123456, tzinfo=datetime.timezone(datetime.timedelta(hours=2), "CEST"))
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert decoded.tzname() == "CEST"

    def test_time_with_zoneinfo_round_trip(self) -> None:
        original = datetime.time(14, 30, 45, 123456, tzinfo=PARIS)
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original
        assert isinstance(decoded.tzinfo, ZoneInfo)
        assert decoded.tzinfo.key == "Europe/Paris"

    # ------------------------------------------------------------------
    # Bare tzinfo objects
    # ------------------------------------------------------------------

    def test_bare_timezone_utc_round_trip(self) -> None:
        decoded = kajson.loads(kajson.dumps(datetime.timezone.utc))
        assert decoded == datetime.timezone.utc

    def test_bare_fixed_offset_timezone_round_trip(self) -> None:
        original = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        decoded = kajson.loads(kajson.dumps(original))
        assert decoded == original

    def test_bare_zoneinfo_round_trip(self) -> None:
        decoded = kajson.loads(kajson.dumps(PARIS))
        assert isinstance(decoded, ZoneInfo)
        assert decoded.key == "Europe/Paris"

    # ------------------------------------------------------------------
    # Wire-format backward compatibility: payloads written by kajson <= 0.6.0
    # ------------------------------------------------------------------

    def test_legacy_datetime_payload_naive(self) -> None:
        legacy_payload = '{"datetime": "2023-12-25 14:30:45.123456", "tzinfo": null, "__class__": "datetime", "__module__": "datetime"}'
        decoded = kajson.loads(legacy_payload)
        assert decoded == datetime.datetime(2023, 12, 25, 14, 30, 45, 123456)
        assert decoded.tzinfo is None

    def test_legacy_datetime_payload_named_zone(self) -> None:
        legacy_payload = '{"datetime": "2023-06-15 10:30:45.123456", "tzinfo": "Europe/Paris", "__class__": "datetime", "__module__": "datetime"}'
        decoded = kajson.loads(legacy_payload)
        assert decoded == datetime.datetime(2023, 6, 15, 10, 30, 45, 123456, tzinfo=PARIS)

    def test_legacy_datetime_payload_fixed_offset_now_decodes(self) -> None:
        """kajson <= 0.6.0 wrote 'UTC+02:00' but could never read it back; now it can."""
        legacy_payload = '{"datetime": "2026-06-10 12:00:00.000000", "tzinfo": "UTC+02:00", "__class__": "datetime", "__module__": "datetime"}'
        decoded = kajson.loads(legacy_payload)
        assert decoded == datetime.datetime(2026, 6, 10, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))

    def test_legacy_datetime_payload_fractional_second_offset_decodes(self) -> None:
        """Legacy names with sub-second offsets (str() of timezone(timedelta(seconds=1.5))) parse too."""
        legacy_payload = (
            '{"datetime": "2026-06-10 12:00:00.000000", "tzinfo": "UTC+00:00:01.500000", "__class__": "datetime", "__module__": "datetime"}'
        )
        decoded = kajson.loads(legacy_payload)
        assert decoded.utcoffset() == datetime.timedelta(seconds=1, microseconds=500000)

    def test_malformed_tzinfo_value_raises_clear_error(self) -> None:
        """A tzinfo value that is neither a string nor a tzinfo object must fail with a clear message."""
        malformed_payload = '{"datetime": "2026-06-10 12:00:00.000000", "tzinfo": {"weird": 1}, "__class__": "datetime", "__module__": "datetime"}'
        with pytest.raises(KajsonDecoderError) as excinfo:
            kajson.loads(malformed_payload)
        assert "expected a string name or a tzinfo object" in str(excinfo.value)

    def test_legacy_time_payload_nested_zoneinfo(self) -> None:
        legacy_payload = (
            '{"time": "14:30:45.123456", "tzinfo": {"zone": "Europe/Paris", "__class__": "ZoneInfo", "__module__": "zoneinfo"}, '
            '"__class__": "time", "__module__": "datetime"}'
        )
        decoded = kajson.loads(legacy_payload)
        assert decoded == datetime.time(14, 30, 45, 123456, tzinfo=PARIS)
