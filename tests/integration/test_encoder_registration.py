# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""Integration tests demonstrating run-time registration of custom encoders
and decoders for "classic" Python types that the standard ``json`` module (and
Pydantic) cannot serialise out-of-the-box.

Each test:
1. Registers a pair of encoder/decoder functions for the target type using
   :pyfunc:`kajson.json_encoder.UniversalJSONEncoder.register` and
   :pyfunc:`kajson.json_decoder.UniversalJSONDecoder.register`.
2. Round-trips an instance of the type through :pyfunc:`kajson.dumps` → string →
   :pyfunc:`kajson.loads` and asserts the recovered object matches the original
   one.
3. Cleans up the registration to avoid leaking state to other tests.

These examples serve as *documentation by example* for library users wishing to
support additional types in their own projects.
"""

from __future__ import annotations

import base64
import decimal
import uuid
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict

from kajson import kajson
from kajson.json_decoder import UniversalJSONDecoder
from kajson.json_encoder import UniversalJSONEncoder


class TestCustomEncoderRegistration:
    """Round-trip tests for dynamically registered encoders/decoders."""

    # ------------------------------------------------------------------
    # Helper – registration management ---------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _register_pair(
        obj_type: type[Any],
        encoder: Callable[[Any], Dict[str, Any]],
        decoder: Callable[[Dict[str, Any]], Any] | None = None,
    ) -> None:
        """Register encoder/decoder and ensure no previously registered pair is lost.

        If a previous encoder or decoder existed for *obj_type* it is restored in
        the caller-controlled teardown via the fixture below.
        """
        TestCustomEncoderRegistration._PREVIOUS_ENCODERS[obj_type] = UniversalJSONEncoder.get_registered_encoder(obj_type)  # type: ignore[index]
        TestCustomEncoderRegistration._PREVIOUS_DECODERS[obj_type] = UniversalJSONDecoder.get_registered_decoder(obj_type)  # type: ignore[index]

        UniversalJSONEncoder.register(obj_type, encoder)
        if decoder is not None:
            UniversalJSONDecoder.register(obj_type, decoder)

    @staticmethod
    def _restore_pair(obj_type: type[Any]) -> None:
        """Re-register previously stored encoder/decoder (or remove if none)."""
        previous_encoder = TestCustomEncoderRegistration._PREVIOUS_ENCODERS.pop(obj_type, None)
        previous_decoder = TestCustomEncoderRegistration._PREVIOUS_DECODERS.pop(obj_type, None)

        if previous_encoder is not None:
            UniversalJSONEncoder.register(obj_type, previous_encoder)
        else:
            # Remove custom encoder we added; ignore if not present
            UniversalJSONEncoder._encoders.pop(obj_type, None)  # pyright: ignore[reportPrivateUsage]

        if previous_decoder is not None:
            UniversalJSONDecoder.register(obj_type, previous_decoder)
        else:
            UniversalJSONDecoder._decoders.pop(obj_type, None)  # pyright: ignore[reportPrivateUsage]

    # Dictionaries to preserve prior state between register/restore calls
    _PREVIOUS_ENCODERS: ClassVar[Dict[type[Any], Any]] = {}
    _PREVIOUS_DECODERS: ClassVar[Dict[type[Any], Any]] = {}

    # ------------------------------------------------------------------
    # Decimal -----------------------------------------------------------
    # ------------------------------------------------------------------

    def test_roundtrip_decimal(self) -> None:
        """Custom (de)serialisation for :class:`decimal.Decimal`."""

        def encode_decimal(value: decimal.Decimal) -> Dict[str, str]:  # type: ignore[name-defined]
            return {"decimal": str(value)}

        def decode_decimal(dct: Dict[str, str]) -> decimal.Decimal:  # type: ignore[name-defined]
            return decimal.Decimal(dct["decimal"])

        self._register_pair(decimal.Decimal, encode_decimal, decode_decimal)
        try:
            original = decimal.Decimal("1234.5678")
            json_str = kajson.dumps(original)
            recovered = kajson.loads(json_str)

            assert recovered == original
            assert isinstance(recovered, decimal.Decimal)
        finally:
            self._restore_pair(decimal.Decimal)

    # ------------------------------------------------------------------
    # UUID --------------------------------------------------------------
    # ------------------------------------------------------------------

    def test_roundtrip_uuid(self) -> None:
        """Custom (de)serialisation for :class:`uuid.UUID`."""

        def encode_uuid(value: uuid.UUID) -> Dict[str, str]:  # type: ignore[name-defined]
            return {"uuid": str(value)}

        def decode_uuid(dct: Dict[str, str]) -> uuid.UUID:  # type: ignore[name-defined]
            return uuid.UUID(dct["uuid"])

        self._register_pair(uuid.UUID, encode_uuid, decode_uuid)
        try:
            original = uuid.uuid4()
            json_str = kajson.dumps(original)
            recovered = kajson.loads(json_str)

            assert recovered == original
            assert isinstance(recovered, uuid.UUID)
        finally:
            self._restore_pair(uuid.UUID)

    # ------------------------------------------------------------------
    # Bytes -------------------------------------------------------------
    # ------------------------------------------------------------------

    def test_roundtrip_bytes(self) -> None:
        """Custom (de)serialisation for :class:`bytes`. Encoded via base64."""

        def encode_bytes(value: bytes) -> Dict[str, str]:
            encoded = base64.b64encode(value).decode()
            return {"bytes_b64": encoded, "__class__": "bytes", "__module__": "builtins"}

        def decode_bytes(dct: Dict[str, str]) -> bytes:
            return base64.b64decode(dct["bytes_b64"].encode())

        self._register_pair(bytes, encode_bytes, decode_bytes)
        try:
            original = b"kajson rules"
            json_str = kajson.dumps(original)
            recovered = kajson.loads(json_str)

            assert recovered == original
            assert isinstance(recovered, bytes)
        finally:
            self._restore_pair(bytes)

    # ------------------------------------------------------------------
    # Set ----------------------------------------------------------------
    # ------------------------------------------------------------------

    def test_roundtrip_set(self) -> None:
        """Custom (de)serialisation for :class:`set`. Represented as list."""

        def encode_set(value: set[Any]) -> Dict[str, Any]:
            return {"items": list(value), "__class__": "set", "__module__": "builtins"}

        def decode_set(dct: Dict[str, Any]) -> set[Any]:
            return set(dct["items"])

        self._register_pair(set, encode_set, decode_set)
        try:
            original: set[int] = {1, 2, 3, 4}
            json_str = kajson.dumps(original)
            recovered = kajson.loads(json_str)

            assert recovered == original
            assert isinstance(recovered, set)
        finally:
            self._restore_pair(set)

    # ------------------------------------------------------------------
    # Path --------------------------------------------------------------
    # ------------------------------------------------------------------

    def test_roundtrip_path(self) -> None:
        """Custom (de)serialisation for :class:`pathlib.Path`."""

        def encode_path(value: Path) -> Dict[str, str]:
            return {"path": str(value), "__class__": "Path", "__module__": "pathlib"}

        def decode_path(dct: Dict[str, str]) -> Path:
            return Path(dct["path"])

        self._register_pair(Path, encode_path, decode_path)
        # Also register for the concrete Path type (PosixPath/WindowsPath)
        concrete_path_type = type(Path())
        if concrete_path_type != Path:
            self._register_pair(concrete_path_type, encode_path, decode_path)
        try:
            original = Path("/tmp/my/test/file.txt")
            json_str = kajson.dumps(original)
            recovered = kajson.loads(json_str)

            assert recovered == original
            assert isinstance(recovered, Path)
        finally:
            self._restore_pair(Path)
            # Also restore concrete Path type if we registered it
            concrete_path_type = type(Path())
            if concrete_path_type != Path:
                self._restore_pair(concrete_path_type)
