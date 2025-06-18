# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from typing import Any, Dict

import pytest
from pydantic import BaseModel

from tests.conftest import SerDeTestCases


class TestSerDePydanticByDict:
    @pytest.mark.parametrize("test_obj, test_obj_dict, test_obj_dict_typed, test_obj_json_str4", SerDeTestCases.PYDANTIC_FULL_CHECKS)
    def test_dump_dict_validate(
        self,
        test_obj: BaseModel,
        test_obj_dict: Dict[str, Any],
        test_obj_dict_typed: Dict[str, Any],
        test_obj_json_str4: str,
    ):
        # Serialize the model to a dictionary
        deserialized_dict = test_obj.model_dump()
        logging.info("Serialized")
        logging.info(deserialized_dict)
        assert deserialized_dict == test_obj_dict_typed

        # Validate the dictionary back to a model
        the_class = type(test_obj)
        deserialized = the_class.model_validate(deserialized_dict)
        logging.info("Deserialized")
        logging.info(deserialized)

        assert test_obj == deserialized

    @pytest.mark.parametrize("test_obj, test_obj_dict, test_obj_dict_typed, test_obj_json_str4", SerDeTestCases.PYDANTIC_FULL_CHECKS)
    def test_serde_dump_json_load_validate(
        self,
        test_obj: BaseModel,
        test_obj_dict: Dict[str, Any],
        test_obj_dict_typed: Dict[str, Any],
        test_obj_json_str4: str,
    ):
        # Serialize the model to a json string
        serialized_str = test_obj.model_dump_json()
        logging.info("Serialized JSON")
        logging.info(serialized_str)

        # Deserialize the json string back to a dictionary
        deserialized_dict = json.loads(serialized_str)
        assert deserialized_dict == test_obj_dict
        logging.info("Deserialized to dict")
        logging.info(deserialized_dict)
        assert deserialized_dict["created_at"] == "2023-01-01T12:00:00"
        assert deserialized_dict["updated_at"] == "2023-01-02T12:13:25"

        # Validate the dictionary back to a model
        the_class = type(test_obj)
        validated_model = the_class.model_validate(deserialized_dict)
        logging.info("Validated model")
        logging.info(validated_model)

        assert test_obj == validated_model
