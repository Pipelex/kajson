# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""Round-trip tests for pydantic dataclasses through kajson.

kajson must treat a pydantic dataclass as a first-class, type-preserving citizen:
encode via its ``__dict__`` (with ``__class__`` / ``__module__`` metadata) and
decode via its pydantic validator. A bad payload must raise ``KajsonDecoderError``
loudly rather than silently falling through to a raw dict.
"""

import json
from datetime import timedelta
from typing import List, Optional, cast

import pytest
from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass

import kajson
from kajson.exceptions import KajsonDecoderError


class NestedModel(BaseModel):
    label: str
    number: int


@pydantic_dataclass
class WithNestedModel:
    title: str
    nested: NestedModel


@pydantic_dataclass
class WithOptional:
    name: str
    note: Optional[str] = None


@pydantic_dataclass
class ListItem:
    index: int
    value: str


@pydantic_dataclass
class WithDataclassList:
    items: List[ListItem]


@pydantic_dataclass
class WithTimedelta:
    name: str
    delay: timedelta


@pydantic_dataclass
class Animal:
    name: str


@pydantic_dataclass
class Dog(Animal):
    breed: str


class TestPydanticDataclassRoundTrip:
    def test_nested_base_model_field(self) -> None:
        obj = WithNestedModel(title="t", nested=NestedModel(label="L", number=3))
        restored = cast(WithNestedModel, kajson.loads(kajson.dumps(obj)))
        assert isinstance(restored, WithNestedModel)
        assert isinstance(restored.nested, NestedModel)
        assert restored == obj

    def test_optional_field_set_and_none(self) -> None:
        for obj in (WithOptional(name="x", note="hi"), WithOptional(name="y")):
            restored = cast(WithOptional, kajson.loads(kajson.dumps(obj)))
            assert isinstance(restored, WithOptional)
            assert restored == obj

    def test_list_of_pydantic_dataclasses(self) -> None:
        obj = WithDataclassList(items=[ListItem(index=0, value="a"), ListItem(index=1, value="b")])
        restored = cast(WithDataclassList, kajson.loads(kajson.dumps(obj)))
        assert isinstance(restored, WithDataclassList)
        assert all(isinstance(item, ListItem) for item in restored.items)
        assert restored == obj

    def test_timedelta_field(self) -> None:
        obj = WithTimedelta(name="x", delay=timedelta(seconds=90))
        restored = cast(WithTimedelta, kajson.loads(kajson.dumps(obj)))
        assert isinstance(restored, WithTimedelta)
        assert restored.delay == timedelta(seconds=90)
        assert restored == obj

    def test_subclass_type_preserved(self) -> None:
        obj = Dog(name="Rex", breed="Lab")
        restored = cast(Animal, kajson.loads(kajson.dumps(obj)))
        assert type(restored) is Dog
        assert restored == obj

    def test_encode_uses_dict_with_class_metadata(self) -> None:
        # Lock the encode-via-__dict__ contract explicitly rather than relying on the
        # generic catch-all: the encoded JSON is the field dict plus class metadata.
        obj = ListItem(index=7, value="z")
        encoded = cast(dict[str, object], json.loads(kajson.dumps(obj)))
        assert encoded == {"index": 7, "value": "z", "__class__": "ListItem", "__module__": __name__}

    def test_bad_payload_raises_decoder_error(self) -> None:
        good = kajson.dumps(ListItem(index=5, value="ok"))
        bad = good.replace('"index": 5', '"index": "not-coercible-zzz"')
        with pytest.raises(KajsonDecoderError):
            kajson.loads(bad)
