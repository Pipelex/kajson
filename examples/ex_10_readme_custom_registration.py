#!/usr/bin/env python3
"""
README Custom Type Registration Example

This example demonstrates how to register custom encoders and decoders
for types like Decimal and Path using the registration system.
"""

from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

import kajson
from kajson import kajson_manager


def main():
    print("=== README Custom Type Registration Example ===\n")

    # Register Decimal support
    def encode_decimal(value: Decimal) -> Dict[str, str]:
        return {"decimal": str(value)}

    def decode_decimal(data: Dict[str, str]) -> Decimal:
        return Decimal(data["decimal"])

    kajson.UniversalJSONEncoder.register(Decimal, encode_decimal)
    kajson.UniversalJSONDecoder.register(Decimal, decode_decimal)

    print("✅ Registered Decimal encoder/decoder")

    # Now Decimal works seamlessly
    data = {"price": Decimal("19.99"), "tax": Decimal("1.50")}
    print(f"Original data: {data}")
    print(f"Price type: {type(data['price'])}")

    json_str = kajson.dumps(data)
    print(f"\nSerialized JSON: {json_str}")

    restored = kajson.loads(json_str)
    print(f"\nRestored data: {restored}")
    print(f"Restored price type: {type(restored['price'])}")

    assert restored["price"] == Decimal("19.99")  # ✅
    print("✅ Decimal values match perfectly!")

    # Register Path support - handle both abstract and concrete types
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

    print("\n✅ Registered Path encoder/decoder")

    # Path objects now work too!
    config = {"home": Path.home(), "config": Path("/etc/myapp/config.json")}
    print(f"Config with paths: {config}")

    restored_config = kajson.loads(kajson.dumps(config))
    print(f"Restored config: {restored_config}")
    print(f"Home path type: {type(restored_config['home'])}")
    print("✅ Path objects work seamlessly!")


if __name__ == "__main__":
    kajson_manager.KajsonManager()
    main()
