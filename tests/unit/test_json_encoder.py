# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import warnings
from typing import Any, Dict

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from kajson.exceptions import UnijsonEncoderError
from kajson.json_encoder import UniversalJSONEncoder, _get_type_module  # pyright: ignore[reportPrivateUsage]


class MockClassWithJsonEncode:
    """Mock class with __json_encode__ method."""

    def __init__(self, data: str):
        self.data = data

    def __json_encode__(self) -> Dict[str, Any]:
        return {"data": self.data}

    @override
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MockClassWithJsonEncode) and self.data == other.data


class MockClassWithFailingJsonEncode:
    """Mock class with __json_encode__ method that fails."""

    def __init__(self, data: str):
        self.data = data

    def __json_encode__(self) -> Dict[str, Any]:
        raise ValueError("Intentional failure in __json_encode__")


class MockClassWithDict:
    """Mock class that uses __dict__ for encoding."""

    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value

    @override
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MockClassWithDict) and self.name == other.name and self.value == other.value


class MockClassWithoutDict:
    """Mock class without __dict__ attribute."""

    __slots__ = ["data"]

    def __init__(self, data: str):
        self.data = data


class MockClassWithoutModule:
    """Mock class that will not have __module__ attribute."""

    def __init__(self, data: str):
        self.data = data


class TestUniversalJSONEncoder:
    """Test cases for UniversalJSONEncoder class."""

    @pytest.fixture(autouse=True)
    def setup_encoder(self) -> None:
        """Set up test fixtures for each test."""
        # Clear any existing encoders
        UniversalJSONEncoder.clear_encoders()
        # Create encoder instance
        self.encoder = UniversalJSONEncoder()

    def teardown_method(self) -> None:
        """Clean up after each test."""
        UniversalJSONEncoder.clear_encoders()

    def test_encoder_initialization(self) -> None:
        """Test encoder initialization sets up logger correctly."""
        encoder = UniversalJSONEncoder()
        assert isinstance(encoder.logger, logging.Logger)
        assert encoder.logger.name == "kajson.encoder"

    def test_log_method(self, mocker: MockerFixture) -> None:
        """Test log method calls logger debug (covers line 72)."""
        mock_debug = mocker.patch.object(self.encoder.logger, "debug")
        self.encoder.log("test message")
        mock_debug.assert_called_once_with("test message")

    def test_register_valid_type_and_function(self) -> None:
        """Test registering a valid type and encoding function."""

        def test_encoder(obj: MockClassWithDict) -> Dict[str, Any]:
            return {"encoded_name": obj.name, "encoded_value": obj.value}

        UniversalJSONEncoder.register(MockClassWithDict, test_encoder)
        assert UniversalJSONEncoder.is_encoder_registered(MockClassWithDict)
        assert UniversalJSONEncoder.get_registered_encoder(MockClassWithDict) is test_encoder

    def test_register_invalid_type_raises_error(self) -> None:
        """Test that registering invalid type raises ValueError (covers line 92)."""

        def test_encoder(data: Dict[str, Any]) -> Dict[str, Any]:
            return data

        with pytest.raises(ValueError) as excinfo:
            UniversalJSONEncoder.register("not_a_type", test_encoder)  # type: ignore[arg-type]

        assert "Expected a type/class" in str(excinfo.value)

    def test_register_invalid_function_raises_error(self) -> None:
        """Test that registering invalid function raises ValueError (covers line 94)."""
        with pytest.raises(ValueError) as excinfo:
            UniversalJSONEncoder.register(MockClassWithDict, "not_a_function")  # type: ignore[arg-type]

        assert "Expected a function" in str(excinfo.value)

    def test_json_dumps_with_builtin_type(self) -> None:
        """Ensure json.dumps works with UniversalJSONEncoder for built-in serialisable types."""
        json_result = json.dumps("test_string", cls=UniversalJSONEncoder)
        assert json_result == '"test_string"'

    def test_default_with_registered_encoder_success(self) -> None:
        """Test default method with successfully registered encoder."""

        def test_encoder(obj: MockClassWithDict) -> Dict[str, Any]:
            return {"encoded_name": obj.name, "encoded_value": obj.value}

        UniversalJSONEncoder.register(MockClassWithDict, test_encoder)

        test_obj = MockClassWithDict("test", 42)
        result = self.encoder.default(test_obj)

        expected = {
            "encoded_name": "test",
            "encoded_value": 42,
            "__class__": "MockClassWithDict",
            "__module__": "tests.unit.test_json_encoder",
        }
        assert result == expected

    def test_default_with_registered_encoder_failure_no_fallback(self) -> None:
        """Test registered encoder failure when fallback disabled (covers lines 130-136)."""

        def failing_encoder(obj: MockClassWithDict) -> Dict[str, Any]:
            raise ValueError("Encoder failed")

        UniversalJSONEncoder.register(MockClassWithDict, failing_encoder)

        test_obj = MockClassWithDict("test", 42)

        with pytest.raises(UnijsonEncoderError) as excinfo:
            self.encoder.default(test_obj)

        assert "Encoding function failing_encoder used for type" in str(excinfo.value)
        assert "raised an exception" in str(excinfo.value)

    def test_default_with_registered_encoder_failure_with_fallback(self, mocker: MockerFixture) -> None:
        """Test registered encoder failure when fallback enabled (covers lines 133-134)."""
        mocker.patch("kajson.json_encoder.IS_ENCODER_FALLBACK_ENABLED", True)

        def failing_encoder(obj: MockClassWithDict) -> Dict[str, Any]:
            raise ValueError("Encoder failed")

        UniversalJSONEncoder.register(MockClassWithDict, failing_encoder)

        test_obj = MockClassWithDict("test", 42)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.encoder.default(test_obj)

            # Should fall back to __dict__ encoding
            assert result["name"] == "test"
            assert result["value"] == 42
            assert result["__class__"] == "MockClassWithDict"
            assert len(w) == 1
            assert "Encoding function failing_encoder used for type" in str(w[0].message)

    def test_default_with_json_encode_method_success(self) -> None:
        """Test default method with successful __json_encode__ method."""
        test_obj = MockClassWithJsonEncode("test_data")
        result = self.encoder.default(test_obj)

        expected = {
            "data": "test_data",
            "__class__": "MockClassWithJsonEncode",
            "__module__": "tests.unit.test_json_encoder",
        }
        assert result == expected

    def test_default_with_json_encode_method_failure_no_fallback(self) -> None:
        """Test __json_encode__ method failure when fallback disabled (covers lines 145-150)."""
        test_obj = MockClassWithFailingJsonEncode("test_data")

        with pytest.raises(UnijsonEncoderError) as excinfo:
            self.encoder.default(test_obj)

        assert "Method __json_encode__() used for type" in str(excinfo.value)
        assert "raised an exception" in str(excinfo.value)

    def test_default_with_json_encode_method_failure_with_fallback(self, mocker: MockerFixture) -> None:
        """Test __json_encode__ method failure when fallback enabled (covers lines 147-148)."""
        mocker.patch("kajson.json_encoder.IS_ENCODER_FALLBACK_ENABLED", True)

        test_obj = MockClassWithFailingJsonEncode("test_data")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.encoder.default(test_obj)

            # Should fall back to __dict__ encoding
            assert result["data"] == "test_data"
            assert result["__class__"] == "MockClassWithFailingJsonEncode"
            assert len(w) == 1
            assert "Method __json_encode__() used for type" in str(w[0].message)

    def test_default_with_dict_fallback_success(self) -> None:
        """Test default method with successful __dict__ fallback."""
        test_obj = MockClassWithDict("test", 42)
        result = self.encoder.default(test_obj)

        expected = {
            "name": "test",
            "value": 42,
            "__class__": "MockClassWithDict",
            "__module__": "tests.unit.test_json_encoder",
        }
        assert result == expected

    def test_default_with_dict_fallback_attribute_error(self) -> None:
        """Test __dict__ fallback when object has no __dict__ (covers line 157)."""
        test_obj = MockClassWithoutDict("test_data")

        with pytest.raises(TypeError) as excinfo:
            self.encoder.default(test_obj)

        assert "is not JSON serializable" in str(excinfo.value)

    def test_default_all_methods_fail_raises_type_error(self) -> None:
        """Test that TypeError is raised when all encoding methods fail (covers line 162)."""
        # Create an object that can't be encoded by any method
        test_obj = MockClassWithoutDict("test_data")

        with pytest.raises(TypeError) as excinfo:
            self.encoder.default(test_obj)

        assert f"Type {type(test_obj)} is not JSON serializable" in str(excinfo.value)

    def test_default_preserves_existing_class_and_module(self) -> None:
        """Test that existing __class__ and __module__ in dict are preserved."""

        class MockWithExistingMetadata:
            def __json_encode__(self) -> Dict[str, Any]:
                return {
                    "data": "test",
                    "__class__": "CustomClass",
                    "__module__": "custom.module",
                }

        test_obj = MockWithExistingMetadata()
        result = self.encoder.default(test_obj)

        assert result["__class__"] == "CustomClass"
        assert result["__module__"] == "custom.module"
        assert result["data"] == "test"

    def test_integration_with_json_dumps(self) -> None:
        """Test integration with json.dumps."""
        test_obj = MockClassWithJsonEncode("test_data")
        json_str = json.dumps(test_obj, cls=UniversalJSONEncoder)

        # Should be valid JSON
        result = json.loads(json_str)
        assert result["data"] == "test_data"
        assert result["__class__"] == "MockClassWithJsonEncode"
        assert result["__module__"] == "tests.unit.test_json_encoder"

    def test_object_module_detection_without_module_attribute(self) -> None:
        """Test module detection when object raises AttributeError for __module__."""

        class MockNoModule(MockClassWithDict):
            """Subclass that raises AttributeError when __module__ is accessed."""

            @property  # type: ignore[override]
            def __module__(self) -> str:  # type: ignore[override]
                raise AttributeError("No __module__ attribute")

        test_obj = MockNoModule("test", 42)

        # Encode the object - this should trigger the fallback to _get_type_module
        result = self.encoder.default(test_obj)
        assert result["__module__"] == ""

    def test_object_module_detection_main_handling(self, mocker: MockerFixture) -> None:
        """Test module detection with __main__ module handling (covers line 191)."""
        # Create object with __main__ as module
        test_obj = MockClassWithDict("test", 42)
        # Modify the class's __module__ attribute to mimic objects defined in __main__
        test_obj.__class__.__module__ = "__main__"  # type: ignore[attr-defined]

        # Mock __main__.__file__ inside json_encoder module
        mock_main = mocker.MagicMock()
        mock_main.__file__ = "/path/to/script.py"
        mocker.patch("kajson.json_encoder.__main__", mock_main)

        result = self.encoder.default(test_obj)
        assert result["__module__"] == "/path/to/script"

    def test_type_module_detection_with_builtin_types(self) -> None:
        """Test _get_type_module directly with built-in types (covers lines 210-218)."""
        # Built-in types return an empty module name
        assert _get_type_module(int) == ""
        assert _get_type_module(str) == ""
        assert _get_type_module(list) == ""

    def test_type_module_detection_with_class_pattern(self) -> None:
        """Test _get_type_module with class pattern (covers lines 213-214)."""
        result = _get_type_module(MockClassWithDict)
        # Depending on the test runner, the module can be '__main__' or the actual test module path
        assert result in {"__main__", "tests.unit.test_json_encoder"}

    def test_type_module_detection_with_type_pattern(self, mocker: MockerFixture) -> None:
        """Test _get_type_module with type pattern (covers lines 215-216)."""
        original_str = str

        def mock_str(obj: Any) -> str:
            if obj is MockClassWithDict:
                return "<type 'some.module.TypeName'>"
            return original_str(obj)

        mocker.patch("kajson.json_encoder.str", side_effect=mock_str)
        assert _get_type_module(MockClassWithDict) == "some.module"

    def test_type_module_detection_fallback_to_builtins(self, mocker: MockerFixture) -> None:
        """Test _get_type_module fallback to builtins when no pattern matches (covers lines 217-218)."""
        original_str = str

        def mock_str(obj: Any) -> str:
            if obj is MockClassWithDict:
                return "<unknown 'SomeWeirdType'>"
            return original_str(obj)

        mocker.patch("kajson.json_encoder.str", side_effect=mock_str)
        assert _get_type_module(MockClassWithDict) == "builtins"
