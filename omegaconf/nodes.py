from abc import abstractmethod

import math
from enum import Enum
from .node import Node
from .errors import ValidationError, UnsupportedValueType
from typing import Optional, Dict


class ValueNode(Node):
    # TODO: parent should be a container (Config [tagging] interface)
    def __init__(self, parent: Optional[Node], is_optional):
        super().__init__(parent=parent)
        assert isinstance(is_optional, bool)
        self.is_optional = is_optional
        self.val = None

    def value(self):
        return self.val

    def set_value(self, value):
        from ._utils import ValueKind, get_value_kind

        if isinstance(value, str) and get_value_kind(value) in (
            ValueKind.INTERPOLATION,
            ValueKind.MANDATORY_MISSING,
        ):
            self.val = value
        else:
            if not self.is_optional and value is None:
                raise ValidationError("Non optional field cannot be assigned None")
            self.val = self.validate_and_convert(value)

    @abstractmethod
    def validate_and_convert(self, value):
        """
        Validates input and converts to canonical form
        :param value: input value
        :return:  converted value ("100" may be converted to 100 for example)
        """
        raise NotImplementedError()

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return repr(self.val)

    def __eq__(self, other):
        if isinstance(other, ValueNode):
            return self.val == other.val and self.is_optional == other.is_optional
        else:
            return self.val == other

    def __ne__(self, other):
        x = self.__eq__(other)
        assert x is not NotImplemented
        return not x


class UntypedNode(ValueNode):
    def __init__(self, value=None, parent: Optional[Node] = None, is_optional=True):
        super().__init__(parent=parent, is_optional=is_optional)
        self.is_optional = True
        self.val = None
        self.set_value(value)

    def validate_and_convert(self, value):
        from ._utils import _valid_input_value_type

        if not _valid_input_value_type(value):
            raise UnsupportedValueType(f"Unsupported value type {value}")
        return value


class StringNode(ValueNode):
    def __init__(self, value=None, parent: Optional[Node] = None, is_optional=True):
        super().__init__(parent=parent, is_optional=is_optional)
        self.val = None
        self.set_value(value)

    def validate_and_convert(self, value):
        return str(value) if value is not None else None


class IntegerNode(ValueNode):
    def __init__(self, value=None, parent: Optional[Node] = None, is_optional=True):
        super().__init__(parent=parent, is_optional=is_optional)
        self.val = None
        self.set_value(value)

    def validate_and_convert(self, value):
        try:
            if value is None:
                val = None
            elif type(value) in (str, int):
                val = int(value)
            else:
                raise ValueError()
        except ValueError:
            raise ValidationError(
                "Value '{}' could not be converted to Integer".format(value)
            )
        return val


class FloatNode(ValueNode):
    def __init__(self, value=None, parent: Optional[Node] = None, is_optional=True):
        super().__init__(parent=parent, is_optional=is_optional)
        self.val = None
        self.set_value(value)

    def validate_and_convert(self, value):
        if value is None:
            return None
        try:
            if type(value) in (float, str, int):
                return float(value)
            else:
                raise ValueError()
        except ValueError:
            raise ValidationError(
                "Value '{}' could not be converted to float".format(value)
            )

    def __eq__(self, other):
        if isinstance(other, ValueNode):
            other_val = other.val
        else:
            other_val = other
        if self.val is None and other is None:
            return True
        if self.val is None and other is not None:
            return False
        if self.val is not None and other is None:
            return False
        return self.val == other_val or (math.isnan(self.val) and math.isnan(other_val))


class BooleanNode(ValueNode):
    def __init__(self, value=None, parent: Optional[Node] = None, is_optional=True):
        super().__init__(parent=parent, is_optional=is_optional)
        self.val = None
        self.set_value(value)

    def validate_and_convert(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        elif value is None:
            return None
        elif isinstance(value, str):
            try:
                return self.validate_and_convert(int(value))
            except ValueError:
                if value.lower() in ("yes", "y", "on", "true"):
                    return True
                elif value.lower() in ("no", "n", "off", "false"):
                    return False
                else:
                    raise ValidationError(
                        "Value '{}' is not a valid bool".format(value)
                    )
        else:
            raise ValidationError(
                "Value '{}' is not a valid bool (type {})".format(
                    value, type(value).__name__
                )
            )


class EnumNode(ValueNode):
    """
    NOTE: EnumNode is serialized to yaml as a string ("Color.BLUE"), not as a fully qualified yaml type.
    this means serialization to YAML of a typed config (with EnumNode) will not retain the type of the Enum
    when loaded.
    This is intentional, Please open an issue against OmegaConf if you wish to discuss this decision.
    """

    def __init__(
        self, enum_type: Enum, parent: Optional[Node] = None, is_optional=True
    ):
        super().__init__(parent=parent, is_optional=is_optional)
        if not isinstance(enum_type, type) or not issubclass(enum_type, Enum):
            raise ValidationError(
                "EnumNode can only operate on Enum subclasses ({})".format(enum_type)
            )
        self.fields: Dict[str, str] = {}
        self.val = None
        self.enum_type: Enum = enum_type
        for name, constant in enum_type.__members__.items():
            self.fields[name] = constant.value

    def validate_and_convert(self, value):
        if value is None:
            return None
        else:
            type_ = type(value)
            if not issubclass(type_, self.enum_type) and type_ not in (str, int,):
                raise ValidationError(
                    "Value {} ({}) is not a valid input for {}".format(
                        value, type_, self.enum_type
                    )
                )

            if isinstance(value, self.enum_type):
                key = value.name
            else:
                try:
                    assert type_ in (str, int)
                    if type_ == str:
                        prefix = "{}.".format(self.enum_type.__name__)
                        if value.startswith(prefix):
                            value = value[len(prefix) :]
                        value = self.enum_type[value]
                    elif type_ == int:
                        value = self.enum_type(value)

                    key = value.name
                except (ValueError, KeyError):
                    raise ValidationError(
                        "Invalid value '{}', expected one of:\n".format(
                            value, "\n".join([f"\t{x}" for x in self.fields])
                        )
                    )

            assert key in self.fields.keys()
            if key in self.fields.keys():
                return value
