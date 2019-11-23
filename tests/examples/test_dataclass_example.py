from enum import Enum

import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from omegaconf import (
    OmegaConf,
    ValidationError,
    MissingMandatoryValue,
    ReadonlyConfigError,
    MISSING,
)


class Height(Enum):
    SHORT = 0
    TALL = 1


@dataclass
class SimpleTypes:
    num: int = 10
    pi: float = 3.1415
    is_awesome: bool = True
    height: Height = Height.SHORT
    description: str = "text"


def test_simple_types_class():
    # Instantiate from a class
    conf = OmegaConf.create(SimpleTypes)
    assert conf.num == 10
    assert conf.pi == 3.1415
    assert conf.is_awesome is True
    assert conf.height == Height.SHORT
    assert conf.description == "text"


def test_static_typing():
    conf: SimpleTypes = OmegaConf.create(SimpleTypes)
    assert conf.description == "text"  # pass static type checking
    with pytest.raises(KeyError):
        # This will fail both the static type checking and at runtime
        # noinspection PyStatementEffect
        conf.no_such_attribute


def test_simple_types_obj():
    # Instantiate from an Object, any value can be overridden
    # at construction
    conf = OmegaConf.create(SimpleTypes(num=20, pi=3))
    assert conf.num == 20
    assert conf.pi == 3
    # Everything not overridden at construction takes the default value
    assert conf.is_awesome is True
    assert conf.height == Height.SHORT
    assert conf.description == "text"


def test_conversions():
    conf = OmegaConf.create(SimpleTypes)

    # OmegaConf can convert types at runtime
    conf.num = 20  # ok, type matches
    conf.num = "20"  # ok, the String "20" is converted to the int 20
    assert conf.num == 20
    with pytest.raises(ValidationError):
        conf.num = "one"  # ValidationError: "one" cannot be converted to an integer

    # booleans can take many forms
    for expected, values in {
        True: ["on", "yes", "true", True, "1"],
        False: ["off", "no", "false", False, "0"],
    }.items():
        for b in values:
            conf.is_awesome = b
            assert conf.is_awesome == expected

    # Enums too
    for expected, values in {
        Height.SHORT: [Height.SHORT, "Height.SHORT", "SHORT", 0],
        Height.TALL: [Height.TALL, "Height.TALL", "TALL", 1],
    }.items():
        for b in values:
            conf.height = b
            assert conf.height == expected


@dataclass
class Modifiers:
    # regular field
    num: int = 10

    # Fields can be optional
    optional_num: Optional[int] = None

    # MISSING fields must be populated at runtime before access. accessing them while they
    # are missing will result in a MissingMandatoryValue exception
    another_num: int = MISSING


def test_modifiers():
    conf: Modifiers = OmegaConf.create(Modifiers)
    # regular fields cannot take None
    with pytest.raises(ValidationError):
        conf.num = None

    # but Optional fields can
    conf.optional_num = None
    assert conf.optional_num is None

    # Accessing a missing field will trigger MissingMandatoryValue exception
    with pytest.raises(MissingMandatoryValue):
        # noinspection PyStatementEffect
        conf.another_num

    # but you can access it once it's been assigned
    conf.another_num = 42
    assert conf.another_num == 42


@dataclass
class User:
    # A simple user class with two missing fields
    name: str = MISSING
    height: Height = MISSING


# Group class contains two instances of User.
@dataclass
class Group:
    name: str = MISSING
    # data classes can be nested
    admin: User = User()

    # You can also specify different defaults for nested classes
    manager: User = User(name="manager", height=Height.TALL)


def test_nesting():
    conf = OmegaConf.create(Group)
    assert conf == {
        "name": "???",
        "admin": {"name": MISSING, "height": MISSING},
        "manager": {"name": "manager", "height": Height.TALL},
    }

    # you can assign a different object of the same type
    conf.admin = User(name="omry", height=Height.TALL)
    with pytest.raises(ValidationError):
        # but not incompatible types
        conf.admin = 10

    with pytest.raises(ValidationError):
        # You can't assign a dict even if the field matches
        conf.manager = {"name": "secret", "height": Height.TALL}


@dataclass
class Lists:
    # List without a specified type. can take any primitive type OmegaConf supports:
    # int, float, bool, str and Enums as well as Any (which is the same as not having a specified type).
    untyped_list: List = field(default_factory=lambda: [1, "foo", True])

    # typed lists can hold int, bool, str, float or enums.
    int_list: List[int] = field(default_factory=lambda: [10, 20, 30])


def test_typed_list_runtime_validation():
    conf = OmegaConf.create(Lists)

    conf.untyped_list[0] = True  # okay, list can hold any primitive type

    conf.int_list[0] = 999  # okay
    assert conf.int_list[0] == 999

    conf.int_list[0] = "1000"  # also ok!
    assert conf.int_list[0] == 1000

    with pytest.raises(ValidationError):
        conf.int_list[0] = "fail"


# Dicts
@dataclass
class Dicts:
    # Dict without specified types.
    # Key must be a string, value can be any primitive type OmegaConf supports:
    # int, float, bool, str and Enums as well as Any (which is the same as not having a specified type).
    untyped_dict: Dict = field(default_factory=lambda: {"foo": True, "bar": 100})

    # maps string to height Enum
    str_to_height: Dict[str, Height] = field(
        default_factory=lambda: {"Yoda": Height.SHORT, "3-CPO": Height.TALL}
    )


def test_typed_dict_runtime_validation():
    conf = OmegaConf.create(Dicts)
    conf.untyped_dict["foo"] = "buzz"  # okay, list can hold any primitive type
    conf.str_to_height["Shorty"] = Height.SHORT  # Okay
    with pytest.raises(ValidationError):
        # runtime failure, cannot convert True to Height
        conf.str_to_height["Yoda"] = True


# Frozen
@dataclass(frozen=True)
class FrozenClass:
    x: int = 10
    list: List = field(default_factory=lambda: [1, 2, 3])


def test_frozen():
    # frozen classes are read only, attempts to modify them at runtime
    # will result in a ReadonlyConfigError
    conf = OmegaConf.create(FrozenClass)
    with pytest.raises(ReadonlyConfigError):
        conf.x = 20

    # Read-only flag is recursive
    with pytest.raises(ReadonlyConfigError):
        conf.list[0] = 20


class Protocol(Enum):
    HTTP = 0
    HTTPS = 1


# TODO: try to enable support for this
# @dataclass
# class Domain:
#     name: str = MISSING
#     path: str = MISSING
#     protocols: List[Protocol] = field(default_factory=lambda: [Protocol.HTTPS])
#
#
# @dataclass
# class WebServer:
#     protocol_ports: Dict[Protocol, int] = field(
#         default_factory=lambda: {Protocol.HTTP: 80, Protocol.HTTPS: 443}
#     )
#     domains: Dict[str, Domain] = field(default_factory=lambda: {})
#
#
# # Merging and overrides
# def test_merging():
#     conf: WebServer = OmegaConf.create(WebServer)
