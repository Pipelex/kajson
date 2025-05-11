# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Dict

import pytest
from pydantic import BaseModel

from kajson import kajson
from kajson.exceptions import KajsonDecoderError

from .conftest import SerDeTestCases, obj_pydantic_tricky_types_json_str4_with_validation_error


class TestSerDeByStr:
    @pytest.mark.parametrize("test_obj", SerDeTestCases.PYDANTIC_EXAMPLES)
    def test_serde_str_pydantic_with_subclasses(self, test_obj: Any):
        # Serialize the model to a json string
        serialized_str: str = kajson.dumps(test_obj, indent=4)  # pyright: ignore[reportUnknownMemberType]
        logging.info("Serialized JSON")
        logging.info(serialized_str)
        deserialized = kajson.loads(serialized_str)  # pyright: ignore[reportUnknownMemberType]
        logging.info(f"Deserialized by kajson as {type(deserialized).__name__}")
        logging.info(deserialized)

        # Assertions to ensure the process worked correctly
        assert test_obj == deserialized

    @pytest.mark.parametrize("test_obj, test_obj_dict, test_obj_dict_typed, test_obj_json_str4", SerDeTestCases.PYDANTIC_FULL_CHECKS)
    def test_serde_str_pydantic_tricky(
        self,
        test_obj: BaseModel,
        test_obj_dict: Dict[str, Any],
        test_obj_dict_typed: Dict[str, Any],
        test_obj_json_str4: str,
    ):
        # Serialize the model to a json string
        serialized_str: str = kajson.dumps(test_obj, indent=4)  # pyright: ignore[reportUnknownMemberType]
        logging.info("Serialized JSON")
        logging.info(serialized_str)
        assert serialized_str == test_obj_json_str4
        deserialized = kajson.loads(serialized_str)  # pyright: ignore[reportUnknownMemberType]
        logging.info(f"Deserialized by kajson as {type(deserialized).__name__}")
        logging.info(deserialized)

        # Assertions to ensure the process worked correctly
        assert test_obj == deserialized

    def test_serde_str_pydantic_validation(self):
        with pytest.raises(KajsonDecoderError) as excinfo:
            deserialized = kajson.loads(obj_pydantic_tricky_types_json_str4_with_validation_error)  # pyright: ignore[reportUnknownMemberType]
            logging.info(f"Deserialized by kajson as {type(deserialized).__name__}")
            logging.info(deserialized)
        assert "using kwargs '<class 'tests.conftest.Number'>': 1 validation error for Number" in str(excinfo.value)
        logging.info(f"Caught expected error: {excinfo.value}")

    @pytest.mark.parametrize("test_obj", SerDeTestCases.ARBITRARY_TYPES)
    def test_serde_str_arbitrary(self, test_obj: Any):
        # Serialize the model to a json string
        serialized_str: str = kajson.dumps(test_obj, indent=4)  # pyright: ignore[reportUnknownMemberType]
        logging.info("Serialized JSON")
        logging.info(serialized_str)
        deserialized = kajson.loads(serialized_str)  # pyright: ignore[reportUnknownMemberType]
        logging.info(f"Deserialized by kajson as {type(deserialized).__name__}")
        logging.info(deserialized)

        # Assertions to ensure the process worked correctly
        assert test_obj == deserialized

    @pytest.mark.parametrize("test_obj", SerDeTestCases.LISTS)
    def test_serde_str_list(self, test_obj: Any):
        # Serialize the model to a json string
        serialized_str: str = kajson.dumps(test_obj, indent=4)  # pyright: ignore[reportUnknownMemberType]
        logging.info("Serialized JSON")
        logging.info(serialized_str)
        deserialized = kajson.loads(serialized_str)  # pyright: ignore[reportUnknownMemberType]
        logging.info(f"Deserialized by kajson as {type(deserialized).__name__}")
        logging.info(deserialized)

        # Assertions to ensure the process worked correctly
        assert test_obj == deserialized
