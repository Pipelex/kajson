# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import datetime
import sys
from typing import Any, cast
from zoneinfo import ZoneInfo

import pytest

import kajson
from kajson.class_registry import ClassRegistry
from kajson.kajson_manager import KajsonManager
from tests.unit.safe_decoding.safe_decoding_classes import (
    Box,
    Color,
    IntListRoot,
    PlainModel,
    PydanticPoint,
    WithJsonDecode,
    WithRegisteredDecoder,
    make_marker,
)


class TestSafeRoundTrips:
    @pytest.mark.parametrize(
        "value",
        [
            PlainModel(name="a", count=2),
            IntListRoot([1, 2, 3]),
            PydanticPoint(abscissa=1, ordinate=2),
            Color.GREEN,
            datetime.datetime(2026, 11, 20, 12, 30, tzinfo=datetime.timezone.utc),
            datetime.datetime(2026, 11, 20, 12, 30, tzinfo=ZoneInfo("Europe/Paris")),
            datetime.date(2026, 11, 20),
            datetime.time(12, 30, 15),
            datetime.timezone(datetime.timedelta(hours=2)),
            datetime.timedelta(days=1, seconds=3, microseconds=5),
        ],
        ids=lambda value: type(value).__name__,
    )
    def test_allowed_kind_round_trips(self, value: Any) -> None:
        assert kajson.loads(kajson.dumps(value), safe=True) == value

    def test_generic_model_round_trips_under_its_subscripted_name(self) -> None:
        encoded = kajson.dumps(Box[int](value=3))
        assert '"Box[int]"' in encoded
        result = kajson.loads(encoded, safe=True)
        assert isinstance(result, Box)
        assert cast(Box[int], result).value == 3

    def test_zone_info_round_trips(self) -> None:
        """ZoneInfo compares by identity, and other tests may clear its cache, so compare keys."""
        result = kajson.loads(kajson.dumps(ZoneInfo("Europe/Paris")), safe=True)
        assert isinstance(result, ZoneInfo)
        assert result.key == "Europe/Paris"

    def test_enum_by_name_and_by_value(self) -> None:
        assert kajson.loads(make_marker("Color", _name_="RED"), safe=True) is Color.RED
        assert kajson.loads(make_marker("Color", _value_="green"), safe=True) is Color.GREEN

    def test_class_with_json_decode_hook(self) -> None:
        result = kajson.loads(kajson.dumps(WithJsonDecode(5)), safe=True)
        assert isinstance(result, WithJsonDecode)
        assert result.value == 5

    @pytest.mark.usefixtures("registered_decoders")
    def test_class_with_registered_decoder(self) -> None:
        result = kajson.loads(make_marker("WithRegisteredDecoder", value=9), safe=True)
        assert isinstance(result, WithRegisteredDecoder)
        assert result.value == 9

    def test_class_from_explicit_registry(self) -> None:
        registry = ClassRegistry()
        registry.register_class(PlainModel, name="Aliased")
        result = kajson.loads(make_marker("Aliased", "nowhere", name="x"), class_registry=registry, safe=True)
        assert result == PlainModel(name="x")

    def test_class_from_global_registry(self) -> None:
        KajsonManager.get_class_registry().register_class(PlainModel, name="GloballyAliased")
        result = kajson.loads(make_marker("GloballyAliased", "not_imported_kajson_module", name="y"), safe=True)
        assert result == PlainModel(name="y")
        assert "not_imported_kajson_module" not in sys.modules

    def test_nested_models_round_trip(self) -> None:
        value = {"items": [PlainModel(name="one"), PlainModel(name="two", count=2)], "when": datetime.date(2026, 1, 2)}
        assert kajson.loads(kajson.dumps(value), safe=True) == value
