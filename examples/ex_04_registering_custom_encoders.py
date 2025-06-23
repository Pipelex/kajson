#!/usr/bin/env python3
"""
Registering Custom Type Encoders Example

This example shows how to register custom encoders and decoders for types
like Decimal and Path that aren't supported by default.
"""

from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

from kajson import kajson, kajson_manager


def main():
    print("=== Registering Custom Type Encoders Example ===\n")

    # Register Decimal support
    kajson.UniversalJSONEncoder.register(Decimal, lambda d: {"decimal": str(d)})
    kajson.UniversalJSONDecoder.register(Decimal, lambda data: Decimal(data["decimal"]))

    # Register Path support - need to handle both abstract Path and concrete types
    def encode_path(p: Path) -> Dict[str, Any]:
        return {"path": str(p)}

    def decode_path(data: Dict[str, Any]) -> Path:
        return Path(data["path"])

    kajson.UniversalJSONEncoder.register(Path, encode_path)
    kajson.UniversalJSONDecoder.register(Path, decode_path)

    # Also register for the concrete Path type (PosixPath/WindowsPath)
    concrete_path_type = type(Path())
    if concrete_path_type != Path:
        kajson.UniversalJSONEncoder.register(concrete_path_type, encode_path)
        kajson.UniversalJSONDecoder.register(concrete_path_type, decode_path)

    print("✅ Registered custom encoders for Decimal and Path")

    # Now they work!
    data = {"price": Decimal("19.99"), "config_path": Path("/etc/app/config.json")}

    print(f"\nOriginal data: {data}")
    print(f"Price type: {type(data['price'])}")
    print(f"Config path type: {type(data['config_path'])}")

    json_str = kajson.dumps(data)
    print(f"\nSerialized JSON: {json_str}")

    restored = kajson.loads(json_str)
    print(f"\nRestored data: {restored}")
    print(f"Restored price type: {type(restored['price'])}")
    print(f"Restored config path type: {type(restored['config_path'])}")

    # Verify types and values
    assert restored["price"] == Decimal("19.99")
    assert isinstance(restored["config_path"], Path)
    print("\n✅ Custom types work perfectly!")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
