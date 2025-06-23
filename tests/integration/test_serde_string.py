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
* Validation errors raised at decode time

Only integration scenarios that are presently required are covered here. New
cases should be added to *tests/test_data.py* and referenced from this file
when needed.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

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
