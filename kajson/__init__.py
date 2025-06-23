# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

# Main API functions (drop-in replacement for json module)
# Exception classes
from kajson.exceptions import (
    ClassRegistryInheritanceError,
    ClassRegistryNotFoundError,
    KajsonDecoderError,
    KajsonException,
    UnijsonEncoderError,
)
from kajson.json_decoder import UniversalJSONDecoder

# Encoder and Decoder classes for custom type registration
from kajson.json_encoder import UniversalJSONEncoder
from kajson.kajson import dump, dumps, load, loads

# Export all main symbols
__all__ = [
    # Main API functions
    "dumps",
    "dump",
    "loads",
    "load",
    # Encoder/Decoder classes
    "UniversalJSONEncoder",
    "UniversalJSONDecoder",
    # Exception classes
    "KajsonException",
    "KajsonDecoderError",
    "ClassRegistryInheritanceError",
    "ClassRegistryNotFoundError",
    "UnijsonEncoderError",
]
