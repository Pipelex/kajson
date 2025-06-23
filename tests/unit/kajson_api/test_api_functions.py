# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import json
from io import StringIO

from pytest_mock import MockerFixture

from kajson import kajson


class TestKajsonAPI:
    """Test cases for kajson API functions (dumps, dump, loads, load)."""

    def test_dumps_basic_object(self) -> None:
        """Test dumps function with basic Python object."""
        test_data = {"key": "value", "number": 42}
        result = kajson.dumps(test_data)

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == test_data

    def test_dumps_with_kwargs(self) -> None:
        """Test dumps function with additional kwargs."""
        test_data = {"key": "value"}
        result = kajson.dumps(test_data, indent=2)

        # Should contain indentation
        assert "  " in result
        parsed = json.loads(result)
        assert parsed == test_data

    def test_dumps_uses_universal_encoder(self, mocker: MockerFixture) -> None:
        """Test that dumps uses UniversalJSONEncoder."""
        mock_dumps = mocker.patch("json.dumps")
        test_data = {"key": "value"}

        kajson.dumps(test_data, indent=2)

        mock_dumps.assert_called_once_with(test_data, cls=kajson.UniversalJSONEncoder, indent=2)

    def test_dump_to_file(self) -> None:
        """Test dump function writes to file object."""
        test_data = {"key": "value", "number": 42}

        with StringIO() as file_obj:
            kajson.dump(test_data, file_obj)
            file_obj.seek(0)
            content = file_obj.read()

        parsed = json.loads(content)
        assert parsed == test_data

    def test_dump_with_kwargs(self) -> None:
        """Test dump function with additional kwargs."""
        test_data = {"key": "value"}

        with StringIO() as file_obj:
            kajson.dump(test_data, file_obj, indent=2)
            file_obj.seek(0)
            content = file_obj.read()

        # Should contain indentation
        assert "  " in content
        parsed = json.loads(content)
        assert parsed == test_data

    def test_dump_uses_universal_encoder(self, mocker: MockerFixture) -> None:
        """Test that dump uses UniversalJSONEncoder."""
        mock_dump = mocker.patch("json.dump")
        test_data = {"key": "value"}
        file_obj = StringIO()

        kajson.dump(test_data, file_obj, indent=2)

        mock_dump.assert_called_once_with(test_data, file_obj, cls=kajson.UniversalJSONEncoder, indent=2)

    def test_loads_basic_json(self) -> None:
        """Test loads function with basic JSON string."""
        json_str = '{"key": "value", "number": 42}'
        result = kajson.loads(json_str)

        expected = {"key": "value", "number": 42}
        assert result == expected

    def test_loads_with_bytes(self) -> None:
        """Test loads function with bytes input (covers line 65)."""
        json_bytes = b'{"key": "value", "number": 42}'
        result = kajson.loads(json_bytes)

        expected = {"key": "value", "number": 42}
        assert result == expected

    def test_loads_with_kwargs(self) -> None:
        """Test loads function with additional kwargs."""
        json_str = '{"key": "value"}'
        result = kajson.loads(json_str)

        assert result == {"key": "value"}

    def test_loads_uses_universal_decoder(self, mocker: MockerFixture) -> None:
        """Test that loads uses UniversalJSONDecoder."""
        mock_loads = mocker.patch("json.loads")
        json_str = '{"key": "value"}'

        kajson.loads(json_str, parse_float=float)

        mock_loads.assert_called_once_with(json_str, cls=kajson.UniversalJSONDecoder, parse_float=float)

    def test_load_from_file(self) -> None:
        """Test load function reads from file object."""
        test_data = {"key": "value", "number": 42}
        json_str = json.dumps(test_data)

        with StringIO(json_str) as file_obj:
            result = kajson.load(file_obj)

        assert result == test_data

    def test_load_with_kwargs(self) -> None:
        """Test load function with additional kwargs."""
        json_str = '{"key": "value"}'

        with StringIO(json_str) as file_obj:
            result = kajson.load(file_obj)

        assert result == {"key": "value"}

    def test_load_uses_universal_decoder(self, mocker: MockerFixture) -> None:
        """Test that load uses UniversalJSONDecoder."""
        mock_load = mocker.patch("json.load")
        file_obj = StringIO('{"key": "value"}')

        kajson.load(file_obj, parse_float=float)

        mock_load.assert_called_once_with(file_obj, cls=kajson.UniversalJSONDecoder, parse_float=float)
