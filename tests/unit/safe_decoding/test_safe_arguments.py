# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, cast

import pytest

import kajson
from kajson.json_decoder import UniversalJSONDecoder


class TestSafeArguments:
    def test_importable_packages_without_safe_raises(self) -> None:
        with pytest.raises(ValueError, match="safe=True"):
            kajson.loads("{}", importable_packages=["pkg"])

    @pytest.mark.parametrize("packages", ["pkg", b"pkg"])
    def test_string_importable_packages_raises(self, packages: Any) -> None:
        with pytest.raises(TypeError, match="single string"):
            kajson.loads("{}", safe=True, importable_packages=packages)

    @pytest.mark.parametrize("packages", [None, 3])
    def test_non_collection_importable_packages_raises(self, packages: Any) -> None:
        with pytest.raises(TypeError, match="collection of package names"):
            kajson.loads("{}", safe=True, importable_packages=packages)

    def test_non_string_entry_raises(self) -> None:
        with pytest.raises(TypeError, match="entries must be strings"):
            kajson.loads("{}", safe=True, importable_packages=cast(Any, [1]))

    @pytest.mark.parametrize("entry", ["", ".pkg", "pkg.", "pkg..sub", "pkg-name", "pkg.*"])
    def test_malformed_entry_raises(self, entry: str) -> None:
        with pytest.raises(ValueError, match="dotted package name"):
            kajson.loads("{}", safe=True, importable_packages=[entry])

    @pytest.mark.parametrize("safe", ["yes", 1, None])
    def test_non_bool_safe_raises(self, safe: Any) -> None:
        with pytest.raises(TypeError, match="safe must be a bool"):
            kajson.loads("{}", safe=safe)

    @pytest.mark.parametrize("packages", [["pkg.sub"], ("pkg.sub",), {"pkg.sub"}, frozenset({"pkg.sub"}), []])
    def test_collections_are_accepted(self, packages: Any) -> None:
        assert kajson.loads('{"a": 1}', safe=True, importable_packages=packages) == {"a": 1}

    def test_decoder_keeps_the_packages_frozen(self) -> None:
        decoder = UniversalJSONDecoder(safe=True, importable_packages=["alpha", "beta.gamma"])
        assert decoder._importable_packages == frozenset({"alpha", "beta.gamma"})  # pyright: ignore[reportPrivateUsage]
