.. _structured_config:

Structured config
-----------------
Structured configs are used to create OmegaConf configuration object with runtime type safety.
In addition, they can be used with tools like mypy or your IDE for static type checking.

Two types of structures classes that are supported: dataclasses and attr classes.

- `dataclasses <https://docs.python.org/3.7/library/dataclasses.html>`_ are standard as of Python 3.7 or newer and are availalbe in Python 3.6 via the `dataclasses` pip package.
- `attrs <https://github.com/python-attrs/attrs>`_ classes are more portable and supports Python as old as Python 2.7, but requires that you install the attrs package. They also have cleaner syntax in some cases but they do add a dependency.

This documentation will use dataclasses. at the bottom there will be a few examples of what things would look like using attrs classes.



.. code-block:: python

    class Height(Enum):
        SHORT = 0
        TALL = 1

    @dataclass
    class User:
        # A simple user class with two fields that are not specified
        name: str = MISSING
        height: Height = MISSING







    @dataclass
    class MyConfig:
        # primitive types
        num: int = 10
        pi: float = 3.14
        is_awesome: bool = True
        height: Height = MISSING
        # This is a missing field, we need to populate it before access
        description: str = "text"

        # MISSING fields must be populated at runtime before access. accessing them while they
        # are missing will result in a MissingMandatoryValue exception
        missing_num: int = MISSING

        # Any primitive field can be optional. Optional fields can take None as a value
        optional_num: Optional[int] = None

        # Containers
        # List without a specified type. can take any primitive type OmegaConf supports:
        # int, float, bool, str and Enums as well as Any (which is the same as not having a specified type).
        untyped_list: List = field(default_factory=lambda: [1, "foo", True])
        # typed lists can hold int, bool, str, float or enums.
        int_list: List[int] = field(default_factory=lambda: [10, 20, 30])

        # Dict without specified types.
        # Key must be a string, value can be any primitive type OmegaConf supports:
        # int, float, bool, str and Enums as well as Any (which is the same as not having a specified type).
        untyped_dict: Dict = field(default_factory=lambda: {"foo": 10, "bar": 20})

        # Maps strings to ints
        name_to_height: Dict[str, Height] = field(
            default_factory=lambda: {"Yoda": Height.SHORT, "3-CPO": Height.TALL}
        )

        # You can nest objects, the default value here is the class.
        # which means fields are still MISSING
        user1: User = User

        # You can also initialize a field. in this case name and age would take the specified values for user2.
        user2: User = User(name="omry", height=Height.TALL)



TODO:
Showing how this can be used in combination with yaml config files (merging from both).

attr.s small example