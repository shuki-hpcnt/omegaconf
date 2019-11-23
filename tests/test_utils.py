from dataclasses import dataclass, field
from enum import Enum

import attr
import pytest
from typing import Any
from typing import List, Dict

# noinspection PyProtectedMember
from omegaconf import _utils
from omegaconf.errors import ValidationError
from . import does_not_raise
from .structured_conf.common import Color


# TODO: complete test coverage for utils


@pytest.mark.parametrize(
    "target_type, value, expectation",
    [
        # Any
        (Any, "foo", does_not_raise()),
        (Any, True, does_not_raise()),
        (Any, 1, does_not_raise()),
        (Any, 1.0, does_not_raise()),
        (Any, Color.RED, does_not_raise()),
        # int
        (int, "foo", pytest.raises(ValidationError)),
        (int, True, pytest.raises(ValidationError)),
        (int, 1, does_not_raise()),
        (int, 1.0, pytest.raises(ValidationError)),
        (int, Color.RED, pytest.raises(ValidationError)),
        # float
        (float, "foo", pytest.raises(ValidationError)),
        (float, True, pytest.raises(ValidationError)),
        (float, 1, does_not_raise()),
        (float, 1.0, does_not_raise()),
        (float, Color.RED, pytest.raises(ValidationError)),
        # bool
        (bool, "foo", pytest.raises(ValidationError)),
        (bool, True, does_not_raise()),
        (bool, 1, does_not_raise()),
        (bool, 0, does_not_raise()),
        (bool, 1.0, pytest.raises(ValidationError)),
        (bool, Color.RED, pytest.raises(ValidationError)),
        (bool, "true", does_not_raise()),
        (bool, "false", does_not_raise()),
        (bool, "on", does_not_raise()),
        (bool, "off", does_not_raise()),
        # str
        (str, "foo", does_not_raise()),
        (str, True, does_not_raise()),
        (str, 1, does_not_raise()),
        (str, 1.0, does_not_raise()),
        (str, Color.RED, does_not_raise()),
        # Color
        (Color, "foo", pytest.raises(ValidationError)),
        (Color, True, pytest.raises(ValidationError)),
        (Color, 1, does_not_raise()),
        (Color, 1.0, pytest.raises(ValidationError)),
        (Color, Color.RED, does_not_raise()),
        (Color, "RED", does_not_raise()),
        (Color, "Color.RED", does_not_raise()),
        # bad type
        (Exception, "nope", pytest.raises(ValueError)),
    ],
)
def test_maybe_wrap(target_type, value, expectation):
    with expectation:
        _utils._maybe_wrap(
            annotated_type=target_type, value=value, is_optional=False, parent=None
        )


class _TestEnum(Enum):
    A = 1
    B = 2


@dataclass
class _TestDataclass:
    x: int = 10
    s: str = "foo"
    b: bool = True
    f: float = 3.14
    e: _TestEnum = _TestEnum.A
    list1: list = field(default_factory=lambda: [])
    list2: List = field(default_factory=lambda: [])
    list3: List[int] = field(default_factory=lambda: [])
    dict1: dict = field(default_factory=lambda: {})
    dict2: Dict = field(default_factory=lambda: {})
    dict3: Dict[str, int] = field(default_factory=lambda: {})


@attr.s(auto_attribs=True)
class _TestAttrsClass:
    x: int = 10
    s: str = "foo"
    b: bool = True
    f: float = 3.14
    e: _TestEnum = _TestEnum.A
    list1: list = []
    list2: List = []
    list3: List[int] = []
    dict1: dict = {}
    dict2: Dict = {}
    dict3: Dict[str, int] = {}


class _TestUserClass:
    pass


@pytest.mark.parametrize(
    "type_, expected",
    [
        (int, True),
        (float, True),
        (bool, True),
        (str, True),
        (Any, True),
        (_TestEnum, True),
        (_TestUserClass, False),
        # Nesting structured configs in contain
        (_TestAttrsClass, False),
        (_TestDataclass, False),
    ],
)
def test_valid_value_annotation_type(type_, expected):
    assert _utils._valid_value_annotation_type(type_) == expected


@pytest.mark.parametrize(
    "test_cls_or_obj, expectation",
    [
        (_TestDataclass, does_not_raise()),
        (_TestDataclass(), does_not_raise()),
        (_TestAttrsClass, does_not_raise()),
        (_TestAttrsClass(), does_not_raise()),
        ("invalid", pytest.raises(ValueError)),
    ],
)
def test_get_structured_config_data(test_cls_or_obj, expectation):
    with expectation:
        d = _utils.get_structured_config_data(test_cls_or_obj)
        assert d["x"] == 10
        assert d["s"] == "foo"
        assert d["b"] == bool(True)
        assert d["f"] == 3.14
        assert d["e"] == _TestEnum.A
        assert d["list1"] == []
        assert d["list2"] == []
        assert d["list3"] == []
        assert d["dict1"] == {}
        assert d["dict2"] == {}
        assert d["dict3"] == {}


def test_is_dataclass(mocker):
    @dataclass
    class Foo:
        pass

    assert _utils.is_dataclass(Foo)
    assert _utils.is_dataclass(Foo())
    assert not _utils.is_dataclass(10)

    mocker.patch("omegaconf._utils.dataclasses", None)
    assert not _utils.is_dataclass(10)


def test_is_attr_class(mocker):
    @attr.s
    class Foo:
        pass

    assert _utils.is_attr_class(Foo)
    assert _utils.is_attr_class(Foo())

    assert not _utils.is_attr_class(10)
    mocker.patch("omegaconf._utils.attr", None)
    assert not _utils.is_attr_class(10)


def test_is_structured_config_frozen_with_invalid_obj():
    with pytest.raises(ValueError):
        _utils.is_structured_config_frozen(10)
