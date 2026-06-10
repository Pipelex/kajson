# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

import sys
import zoneinfo
from typing import Iterator

import pytest


@pytest.fixture
def no_tz_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Simulate a host with no timezone database at all.

    Hides both sources zoneinfo can read from:
    - system tz files (e.g. /usr/share/zoneinfo), via reset_tzpath(to=[])
    - the tzdata pip package, by blocking its import (a None entry in
      sys.modules makes `import tzdata` raise ImportError)

    This reproduces a bare container running a python-build-standalone
    interpreter, or a Windows host without the tzdata package: any
    ZoneInfo(key) lookup raises ZoneInfoNotFoundError. ZoneInfo objects
    created *before* the fixture activates keep working (their data is
    already in memory), which mirrors real cross-process payloads: the
    encoding host had the zone, the decoding host does not.
    """
    for module_name in [name for name in sys.modules if name == "tzdata" or name.startswith("tzdata.")]:
        monkeypatch.delitem(sys.modules, module_name)
    monkeypatch.setitem(sys.modules, "tzdata", None)  # pyright: ignore[reportArgumentType]
    original_tzpath = tuple(zoneinfo.TZPATH)
    zoneinfo.reset_tzpath(to=[])
    zoneinfo.ZoneInfo.clear_cache()
    try:
        yield
    finally:
        zoneinfo.reset_tzpath(to=original_tzpath)
        zoneinfo.ZoneInfo.clear_cache()
