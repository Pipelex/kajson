# SPDX-FileCopyrightText: © 2025-2026 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0

"""Round-trip tests for pydantic dataclasses through kajson.

kajson must treat a pydantic dataclass as a first-class, type-preserving citizen:
encode via its ``__dict__`` (with ``__class__`` / ``__module__`` metadata) and
decode via its pydantic validator. A bad payload must raise ``KajsonDecoderError``
loudly rather than silently falling through to a raw dict.

Known limitation: a ``field(init=False)`` attribute set imperatively to a value
that diverges from its default (or its ``__post_init__`` result) is NOT preserved
across a round-trip. Decoding reconstructs through the constructor, and pydantic
silently ignores ``init=False`` kwargs, so the field falls back to its default.
See ``test_init_false_field_not_preserved``.
"""

import json
from dataclasses import field
from datetime import timedelta
from typing import List, Optional, cast

import pytest
from pydantic import BaseModel, field_validator
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


@pydantic_dataclass
class WithPostInitGuard:
    value: int

    def __post_init__(self) -> None:
        # RuntimeError (unlike ValueError) is NOT wrapped into pydantic's ValidationError,
        # so it exercises the non-ValidationError escape route from the decoder branch.
        if self.value < 0:
            raise RuntimeError("value must be non-negative")


@pydantic_dataclass
class WithFieldValidator:
    amount: int

    @field_validator("amount")
    @classmethod
    def _amount_non_negative(cls, value: int) -> int:
        # A @field_validator raising ValueError IS wrapped into pydantic's ValidationError,
        # exercising the validation-rejection path of the decoder branch (distinct from
        # built-in coercion failures and from __post_init__ raising a raw RuntimeError).
        if value < 0:
            raise ValueError("amount must be non-negative")
        return value


class OuterModelWithDataclassField(BaseModel):
    tag: str
    item: ListItem


@pydantic_dataclass
class EmptyDataclass:
    pass


@pydantic_dataclass
class WithInitFalseField:
    name: str
    cached: int = field(init=False, default=0)


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

    def test_non_validation_error_in_post_init_raises_decoder_error(self) -> None:
        # A __post_init__ raising a non-ValidationError (here RuntimeError) must still be
        # reported as KajsonDecoderError, not leak the raw exception out of kajson.loads().
        good = kajson.dumps(WithPostInitGuard(value=5))
        bad = good.replace('"value": 5', '"value": -1')
        with pytest.raises(KajsonDecoderError):
            kajson.loads(bad)

    def test_field_validator_rejection_raises_decoder_error(self) -> None:
        good = kajson.dumps(WithFieldValidator(amount=5))
        bad = good.replace('"amount": 5', '"amount": -1')
        with pytest.raises(KajsonDecoderError):
            kajson.loads(bad)

    def test_pydantic_dataclass_as_base_model_field(self) -> None:
        obj = OuterModelWithDataclassField(tag="t", item=ListItem(index=1, value="v"))
        restored = cast(OuterModelWithDataclassField, kajson.loads(kajson.dumps(obj)))
        assert isinstance(restored, OuterModelWithDataclassField)
        assert isinstance(restored.item, ListItem)
        assert restored == obj

    def test_empty_dataclass_round_trip(self) -> None:
        obj = EmptyDataclass()
        restored = kajson.loads(kajson.dumps(obj))
        assert isinstance(restored, EmptyDataclass)

    def test_init_false_field_not_preserved(self) -> None:
        # Locks the documented known limitation (see module docstring): an init=False field
        # set imperatively to a value that diverges from its default is lost on round-trip.
        # The decoder reconstructs through the constructor, and pydantic silently ignores
        # init=False kwargs, so the field falls back to its default rather than 7.
        obj = WithInitFalseField(name="x")
        obj.cached = 7
        restored = cast(WithInitFalseField, kajson.loads(kajson.dumps(obj)))
        assert isinstance(restored, WithInitFalseField)
        assert restored.name == "x"
        assert restored.cached == 0
