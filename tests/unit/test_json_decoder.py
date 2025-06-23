# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import sys
import warnings
from typing import Any, Dict, Generator

import pytest
from pydantic import BaseModel, Field, RootModel, ValidationError
from pytest_mock import MockerFixture
from typing_extensions import override

from kajson.exceptions import KajsonDecoderError
from kajson.json_decoder import UniversalJSONDecoder


class MockModelValid(BaseModel):
    """Mock BaseModel for successful validation."""

    name: str
    value: int = Field(ge=0)


class MockModelInvalid(BaseModel):
    """Mock BaseModel that will fail validation."""

    name: str
    value: int = Field(ge=100)  # Will fail with values < 100


class MockRootModelValid(RootModel[Dict[str, Any]]):
    """Mock RootModel for successful validation."""

    pass


class MockRootModelInvalid(RootModel[str]):
    """Mock RootModel that will fail validation."""

    pass


class MockClassWithJsonDecode:
    """Mock class with __json_decode__ method."""

    def __init__(self, data: str):
        self.data = data

    @classmethod
    def __json_decode__(cls, the_dict: Dict[str, Any]) -> "MockClassWithJsonDecode":
        return cls(the_dict["data"])

    @override
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MockClassWithJsonDecode) and self.data == other.data


class MockClassWithFailingJsonDecode:
    """Mock class with __json_decode__ method that fails."""

    def __init__(self, data: str):
        self.data = data

    @classmethod
    def __json_decode__(cls, the_dict: Dict[str, Any]) -> "MockClassWithFailingJsonDecode":
        raise ValueError("Intentional failure in __json_decode__")


class MockClassWithDictConstructor:
    """Mock class that accepts dict as constructor argument."""

    def __init__(self, **kwargs: Any):
        self.data = kwargs

    @override
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MockClassWithDictConstructor) and self.data == other.data


class MockClassWithDefaultConstructor:
    """Mock class with default constructor."""

    def __init__(self) -> None:
        self.initialized = True

    @override
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MockClassWithDefaultConstructor) and hasattr(other, "initialized")


class MockClassWithFailingConstructor:
    """Mock class with constructor that fails."""

    def __init__(self, **kwargs: Any) -> None:
        raise ValueError("Constructor always fails")


@pytest.fixture(autouse=True)
def setup_decoder() -> Generator[UniversalJSONDecoder, None, None]:
    """Set up test fixtures for each test."""
    # Clear any existing decoders
    UniversalJSONDecoder.clear_decoders()
    # Create decoder instance
    decoder = UniversalJSONDecoder()
    yield decoder
    # Clean up after each test
    UniversalJSONDecoder.clear_decoders()


class TestUniversalJSONDecoder:
    """Test cases for UniversalJSONDecoder class."""

    def test_register_valid_type_and_function(self) -> None:
        """Test registering a valid type and decoding function."""

        def test_decoder(data: Dict[str, Any]) -> str:
            return f"decoded_{data['value']}"

        UniversalJSONDecoder.register(str, test_decoder)
        assert UniversalJSONDecoder.is_decoder_registered(str)
        assert UniversalJSONDecoder.get_registered_decoder(str) is test_decoder

    def test_register_invalid_type_raises_error(self) -> None:
        """Test that registering invalid type raises TypeError."""

        def test_decoder(data: Dict[str, Any]) -> str:
            return "test"

        with pytest.raises(TypeError) as excinfo:
            UniversalJSONDecoder.register("not_a_type", test_decoder)  # type: ignore[arg-type]

        assert "Expected a type/class" in str(excinfo.value)

    def test_register_invalid_function_raises_error(self) -> None:
        """Test that registering invalid function raises TypeError."""
        with pytest.raises(TypeError) as excinfo:
            UniversalJSONDecoder.register(str, "not_a_function")  # type: ignore[arg-type]

        assert "Expected a function" in str(excinfo.value)

    def test_universal_decoder_no_class_key(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder returns dict as-is when no __class__ key."""
        test_dict = {"key": "value", "number": 42}
        result = setup_decoder.universal_decoder(test_dict)
        assert result == test_dict

    def test_universal_decoder_with_sys_modules(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder using class from sys.modules."""
        # Use a built-in class that's already in sys.modules
        test_dict = {"__class__": "dict", "__module__": "builtins", "test_key": "test_value"}
        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, dict)
        assert result == {"test_key": "test_value"}

    def test_universal_decoder_with_registry(self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture) -> None:
        """Test decoder using class from registry."""
        mock_registry_instance = mocker.MagicMock()
        mock_registry_instance.get_class.return_value = MockClassWithDictConstructor
        mock_registry = mocker.patch("kajson.kajson_manager.KajsonManager.get_class_registry")
        mock_registry.return_value = mock_registry_instance

        test_dict = {"__class__": "MockClassWithDictConstructor", "__module__": "test_module", "data": "test_data"}
        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, MockClassWithDictConstructor)

    def test_universal_decoder_import_module_failure(self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture) -> None:
        """Test decoder handles import module failure."""
        mock_import = mocker.patch("importlib.import_module")
        mock_import.side_effect = ImportError("Module not found")

        test_dict = {"__class__": "NonExistentClass", "__module__": "non_existent_module", "data": "test"}

        with pytest.raises(KajsonDecoderError) as excinfo:
            setup_decoder.universal_decoder(test_dict)

        assert "Error while trying to import module" in str(excinfo.value)

    def test_universal_decoder_registered_decoder_success(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with successfully registered decoder."""

        def test_decoder(data: Dict[str, Any]) -> str:
            return f"decoded_{data['value']}"

        UniversalJSONDecoder.register(str, test_decoder)

        test_dict = {"__class__": "str", "__module__": "builtins", "value": "test"}

        result = setup_decoder.universal_decoder(test_dict)
        assert result == "decoded_test"

    def test_universal_decoder_registered_decoder_failure_no_fallback(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with failing registered decoder when fallback disabled."""

        def failing_decoder(data: Dict[str, Any]) -> str:
            raise ValueError("Decoder failed")

        UniversalJSONDecoder.register(str, failing_decoder)

        test_dict = {"__class__": "str", "__module__": "builtins", "value": "test"}

        with pytest.raises(KajsonDecoderError) as excinfo:
            setup_decoder.universal_decoder(test_dict)

        assert "Could not decode 'str' from json because function 'failing_decoder' failed" in str(excinfo.value)

    def test_universal_decoder_registered_decoder_failure_with_fallback(self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture) -> None:
        """Test decoder with failing registered decoder when fallback enabled."""
        mocker.patch("kajson.json_decoder.IS_DECODER_FALLBACK_ENABLED", True)

        def failing_decoder(data: Dict[str, Any]) -> str:
            raise ValueError("Decoder failed")

        UniversalJSONDecoder.register(str, failing_decoder)

        test_dict = {"__class__": "str", "__module__": "builtins", "value": "test"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = setup_decoder.universal_decoder(test_dict)
            # Should fall back to next decoding method - returns dict since no __json_decode__ method
            assert isinstance(result, dict)
            assert len(w) == 1
            assert "Could not decode 'str' from json because function 'failing_decoder' failed" in str(w[0].message)

    def test_universal_decoder_json_decode_method_success(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with successful __json_decode__ method."""
        test_dict = {"__class__": "MockClassWithJsonDecode", "__module__": "tests.unit.test_json_decoder", "data": "test_data"}

        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, MockClassWithJsonDecode)
        assert result.data == "test_data"

    def test_universal_decoder_json_decode_method_failure_no_fallback(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with failing __json_decode__ method when fallback disabled."""
        test_dict = {"__class__": "MockClassWithFailingJsonDecode", "__module__": "tests.unit.test_json_decoder", "data": "test_data"}

        with pytest.raises(KajsonDecoderError) as excinfo:
            setup_decoder.universal_decoder(test_dict)

        assert "Could not decode 'MockClassWithFailingJsonDecode' from json because static method __json_decode__ failed" in str(excinfo.value)

    def test_universal_decoder_json_decode_method_failure_with_fallback(self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture) -> None:
        """Test decoder with failing __json_decode__ method when fallback enabled."""
        mocker.patch("kajson.json_decoder.IS_DECODER_FALLBACK_ENABLED", True)

        test_dict = {"__class__": "MockClassWithFailingJsonDecode", "__module__": "tests.unit.test_json_decoder", "data": "test_data"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = setup_decoder.universal_decoder(test_dict)
            # Should fall back to next decoding method (constructor with dict)
            assert isinstance(result, MockClassWithFailingJsonDecode)
            assert len(w) == 1
            assert "Could not decode 'MockClassWithFailingJsonDecode' from json because static method __json_decode__ failed" in str(w[0].message)

    def test_universal_decoder_root_model_success(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with successful RootModel."""
        test_dict = {"__class__": "MockRootModelValid", "__module__": "tests.unit.test_json_decoder", "root": {"key": "value"}}

        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, MockRootModelValid)

    def test_universal_decoder_root_model_creation_failure(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with RootModel creation failure."""
        test_dict = {
            "__class__": "MockRootModelInvalid",
            "__module__": "tests.unit.test_json_decoder",
            "root": {"invalid": "data"},  # Should be string for MockRootModelInvalid
        }

        with pytest.raises(KajsonDecoderError) as excinfo:
            setup_decoder.universal_decoder(test_dict)

        assert "Could not decode 'MockRootModelInvalid' pydantic RootModel from json" in str(excinfo.value)

    def test_universal_decoder_root_model_validation_failure(self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture) -> None:
        """Test decoder with RootModel post-validation failure."""
        # Create a scenario where the model is created but validation fails
        mock_validate = mocker.patch.object(MockRootModelValid, "model_validate")
        mock_validate.side_effect = ValidationError.from_exception_data("MockRootModelValid", [])

        test_dict = {"__class__": "MockRootModelValid", "__module__": "tests.unit.test_json_decoder", "root": {"key": "value"}}

        with pytest.raises(KajsonDecoderError) as excinfo:
            setup_decoder.universal_decoder(test_dict)

        assert "Could not post validate pydantic RootModel" in str(excinfo.value)

    def test_universal_decoder_base_model_success(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with successful BaseModel."""
        test_dict = {"__class__": "MockModelValid", "__module__": "tests.unit.test_json_decoder", "name": "test", "value": 42}

        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, MockModelValid)
        assert result.name == "test"
        assert result.value == 42

    def test_universal_decoder_base_model_validation_failure_with_constructor_success(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with BaseModel validation failure but constructor success."""
        test_dict = {
            "__class__": "MockModelInvalid",
            "__module__": "tests.unit.test_json_decoder",
            "name": "test",
            "value": 150,  # Valid for constructor, passes validation
        }

        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, MockModelInvalid)
        assert result.name == "test"
        assert result.value == 150

    def test_universal_decoder_base_model_all_validation_failures(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with BaseModel where all validation methods fail."""
        test_dict = {
            "__class__": "MockModelInvalid",
            "__module__": "tests.unit.test_json_decoder",
            "name": "test",
            "value": 50,  # Too small, will fail validation
        }

        with pytest.raises(KajsonDecoderError) as excinfo:
            setup_decoder.universal_decoder(test_dict)

        assert "Could not instantiate pydantic BaseModel" in str(excinfo.value)

    def test_universal_decoder_base_model_constructor_success_validation_failure(
        self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture
    ) -> None:
        """Test decoder with BaseModel constructor success but post-validation failure."""
        # Mock the constructor to succeed and post-validation to fail
        mocker.patch.object(MockModelValid, "__init__", return_value=None)

        # Mock model_validate to fail both times (first call and second call during validation)
        mocker.patch.object(
            MockModelValid,
            "model_validate",
            side_effect=[
                ValidationError.from_exception_data("MockModelValid", []),  # First call fails
                ValidationError.from_exception_data("MockModelValid", []),  # Second call fails
            ],
        )

        test_dict = {"__class__": "MockModelValid", "__module__": "tests.unit.test_json_decoder", "name": "test", "value": 42}

        with pytest.raises(KajsonDecoderError) as excinfo:
            setup_decoder.universal_decoder(test_dict)

        assert "Could not post validate pydantic BaseModel" in str(excinfo.value)

    def test_universal_decoder_constructor_with_dict_success(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with constructor accepting dictionary arguments."""
        test_dict = {"__class__": "MockClassWithDictConstructor", "__module__": "tests.unit.test_json_decoder", "key1": "value1", "key2": "value2"}

        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, MockClassWithDictConstructor)
        assert result.data == {"key1": "value1", "key2": "value2"}

    def test_universal_decoder_default_constructor_success(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder with default constructor and __dict__ replacement."""
        test_dict = {"__class__": "MockClassWithDefaultConstructor", "__module__": "tests.unit.test_json_decoder", "custom_attr": "custom_value"}

        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, MockClassWithDefaultConstructor)
        assert result.custom_attr == "custom_value"  # type: ignore[attr-defined]

    def test_universal_decoder_all_methods_fail_return_dict(self, setup_decoder: UniversalJSONDecoder) -> None:
        """Test decoder returns raw dict when all decoding methods fail."""
        # Create a class that will fail both constructor methods
        test_dict = {"__class__": "MockClassWithFailingConstructor", "__module__": "tests.unit.test_json_decoder", "data": "test"}

        result = setup_decoder.universal_decoder(test_dict)
        # Should return the raw dict with __class__ and __module__ keys removed
        assert result == {"data": "test"}

    def test_decoder_initialization(self) -> None:
        """Test decoder initialization sets up logger correctly."""
        decoder = UniversalJSONDecoder()
        assert isinstance(decoder.logger, logging.Logger)
        assert decoder.logger.name == "kajson.decoder"

    def test_log_method(self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture) -> None:
        """Test log method calls logger debug."""
        mock_debug = mocker.patch.object(setup_decoder.logger, "debug")
        setup_decoder.log("test message")
        mock_debug.assert_called_once_with("test message")

    def test_integration_with_json_loads(self) -> None:
        """Test integration with json.loads."""
        test_obj = MockClassWithJsonDecode("test_data")
        test_json = json.dumps({"__class__": "MockClassWithJsonDecode", "__module__": "tests.unit.test_json_decoder", "data": "test_data"})

        result = json.loads(test_json, cls=UniversalJSONDecoder)
        assert result == test_obj

    def test_universal_decoder_successful_module_import(self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture) -> None:
        """Test decoder with successful module import (covers lines 150-151)."""
        # Mock the registry to return None, forcing module import
        mock_registry_instance = mocker.MagicMock()
        mock_registry_instance.get_class.return_value = None
        mock_registry = mocker.patch("kajson.kajson_manager.KajsonManager.get_class_registry")
        mock_registry.return_value = mock_registry_instance

        # Use a module that exists but needs to be imported (datetime is a good example)
        # Remove datetime from sys.modules temporarily to force import
        datetime_module = sys.modules.pop("datetime", None)

        try:
            test_dict = {"__class__": "datetime", "__module__": "datetime", "year": 2023, "month": 1, "day": 1}

            result = setup_decoder.universal_decoder(test_dict)
            # Should successfully create datetime object using constructor
            import datetime as dt

            assert isinstance(result, dt.datetime)
            assert result.year == 2023
            assert result.month == 1
            assert result.day == 1
        finally:
            # Restore datetime module if it existed
            if datetime_module is not None:
                sys.modules["datetime"] = datetime_module

    def test_universal_decoder_base_model_constructor_and_validation_success(
        self, setup_decoder: UniversalJSONDecoder, mocker: MockerFixture
    ) -> None:
        """Test decoder with BaseModel constructor success and validation success (covers lines 218-219)."""
        # Create a scenario where model_validate initially fails, but constructor succeeds and subsequent validation passes
        validation_call_count = 0

        def mock_model_validate(*args: Any, **kwargs: Any) -> Any:
            nonlocal validation_call_count
            validation_call_count += 1
            if validation_call_count == 1:
                # First call (direct validation) fails
                raise ValidationError.from_exception_data("MockModelValid", [])
            else:
                # Second call (after constructor) succeeds
                if "obj" in kwargs:
                    return kwargs["obj"]
                elif args:
                    return args[0]
                return None

        mocker.patch.object(MockModelValid, "model_validate", side_effect=mock_model_validate)

        test_dict = {"__class__": "MockModelValid", "__module__": "tests.unit.test_json_decoder", "name": "test", "value": 42}

        result = setup_decoder.universal_decoder(test_dict)
        assert isinstance(result, MockModelValid)
        assert result.name == "test"
        assert result.value == 42
