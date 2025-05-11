# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Dict

import pytest
from pydantic import BaseModel

from kajson import kajson

from .conftest import SerDeTestCases


class TestSerDePydanticByStr:
    @pytest.mark.parametrize("test_obj, test_obj_json_str4", SerDeTestCases.PYDANTIC_STR_CHECKS)
    def test_serialize_to_string_and_deserialize(
        self,
        test_obj: BaseModel,
        test_obj_json_str4: str,
    ):
        """
        Test serialization of Pydantic models to string and deserialization back using kajson.

        Args:
            test_obj: The Pydantic model to test
            test_obj_json_str4: The expected JSON string representation
        """
        # Serialize the model to a string using kajson
        serialized_str = kajson.dumps(test_obj, indent=4)
        logging.info("Serialized")
        logging.info(serialized_str)

        # Convert dict to string representation for comparison
        assert serialized_str == test_obj_json_str4

        # Deserialize the string back to a model
        deserialized = kajson.loads(serialized_str)
        logging.info("Deserialized")
        logging.info(deserialized)

        assert test_obj == deserialized
