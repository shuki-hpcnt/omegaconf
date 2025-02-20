.. testsetup:: *

    from omegaconf import OmegaConf
    import os
    import sys
    os.environ['USER'] = 'omry'

.. testsetup:: loaded

    from omegaconf import OmegaConf
    conf = OmegaConf.load('source/example.yaml')

Installation
------------

Just pip install::

    pip install omegaconf

Creating
--------
Empty
^^^^^

.. doctest::

    >>> from omegaconf import OmegaConf
    >>> conf = OmegaConf.create()
    >>> print(conf.pretty())
    {}
    <BLANKLINE>

From a dictionary
^^^^^^^^^^^^^^^^^

.. doctest::

    >>> conf = OmegaConf.create(dict(k='v',list=[1,dict(a='1',b='2')]))
    >>> print(conf.pretty())
    k: v
    list:
    - 1
    - a: '1'
      b: '2'
    <BLANKLINE>

From a list
^^^^^^^^^^^

.. doctest::

    >>> conf = OmegaConf.create([1, dict(a=10, b=dict(a=10))])
    >>> print(conf.pretty())
    - 1
    - a: 10
      b:
        a: 10
    <BLANKLINE>

From a yaml file
^^^^^^^^^^^^^^^^

.. doctest::

    >>> conf = OmegaConf.load('source/example.yaml')
    >>> # Output is identical to the yaml file
    >>> print(conf.pretty())
    log:
      file: ???
      rotation: 3600
    server:
      port: 80
    users:
    - user1
    - user2
    <BLANKLINE>


From a yaml string
^^^^^^^^^^^^^^^^^^

.. doctest::

    >>> conf = OmegaConf.create("a: b\nb: c\nlist:\n- item1\n- item2\n")
    >>> print(conf.pretty())
    a: b
    b: c
    list:
    - item1
    - item2
    <BLANKLINE>

From a dot-list
^^^^^^^^^^^^^^^^

.. doctest::

    >>> dot_list = ["a.aa.aaa=1", "a.aa.bbb=2", "a.bb.aaa=3", "a.bb.bbb=4"]
    >>> conf = OmegaConf.from_dotlist(dot_list)
    >>> print(conf.pretty())
    a:
      aa:
        aaa: 1
        bbb: 2
      bb:
        aaa: 3
        bbb: 4
    <BLANKLINE>

From command line arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To parse the content of sys.arg:

.. doctest::

    >>> # Simulating command line arguments
    >>> sys.argv = ['your-program.py', 'server.port=82', 'log.file=log2.txt']
    >>> conf = OmegaConf.from_cli()
    >>> print(conf.pretty())
    log:
      file: log2.txt
    server:
      port: 82
    <BLANKLINE>

Access and manipulation
-----------------------

Input yaml file for this section:

.. literalinclude:: example.yaml
   :language: yaml

Access
^^^^^^

.. doctest:: loaded

    >>> # object style access of dictionary elements
    >>> conf.server.port
    80

    >>> # dictionary style access
    >>> conf['log']['rotation']
    3600

    >>> # items in list
    >>> conf.users[0]
    'user1'

Default values
^^^^^^^^^^^^^^
You can provided default values directly in the accessing code:

.. doctest:: loaded

    >>> # providing default values
    >>> conf.missing_key or 'a default value'
    'a default value'

    >>> conf.get('missing_key', 'a default value')
    'a default value'

Mandatory values
^^^^^^^^^^^^^^^^
Use the value ??? to indicate parameters that need to be set prior to access

.. doctest:: loaded

    >>> conf.log.file
    Traceback (most recent call last):
    ...
    omegaconf.MissingMandatoryValue: log.file


Manipulation
^^^^^^^^^^^^
.. doctest:: loaded

    >>> # Changing existing keys
    >>> conf.server.port = 81

    >>> # Adding new keys
    >>> conf.server.hostname = "localhost"

    >>> # Adding a new dictionary
    >>> conf.database = {'hostname': 'database01', 'port': 3306}


Variable interpolation
----------------------

OmegaConf support variable interpolation, Interpolations are evaluated lazily on access.

Config node interpolation
^^^^^^^^^^^^^^^^^^^^^^^^^
The interpolated variable can be the dot-path to another node in the configuration, and in that case
the value will be the value of that node.

Input yaml file:

.. include:: config_interpolation.yaml
   :code: yaml


Example:

.. doctest::

    >>> conf = OmegaConf.load('source/config_interpolation.yaml')
    >>> # Primitive interpolation types are inherited from the referenced value
    >>> print(conf.client.server_port)
    80
    >>> print(type(conf.client.server_port).__name__)
    int

    >>> # Composite interpolation types are always string
    >>> print(conf.client.url)
    http://localhost:80/
    >>> print(type(conf.client.url).__name__)
    str


Environment variable interpolation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Environment variable interpolation is also supported.

Input yaml file:

.. include:: env_interpolation.yaml
   :code: yaml

.. doctest::

    >>> conf = OmegaConf.load('source/env_interpolation.yaml')
    >>> print(conf.user.name)
    omry
    >>> print(conf.user.home)
    /home/omry


Custom interpolations
^^^^^^^^^^^^^^^^^^^^^
You can add additional interpolation types using custom resolvers.
This example creates a resolver that adds 10 the the given value.

.. doctest::

    >>> OmegaConf.register_resolver("plus_10", lambda x: int(x) + 10)
    >>> c = OmegaConf.create({'key': '${plus_10:990}'})
    >>> c.key
    1000


Custom resolvers support variadic argument lists in the form of a comma separated list of zero or more values (coming in OmegaConf 1.3.1).
Whitespaces are stripped from both ends of each value ("foo,bar" is the same as "foo, bar ").
You can use literal commas and spaces anywhere by escaping (:code:`\,` and :code:`\ `).
.. doctest::

    >>> OmegaConf.register_resolver("concat", lambda x,y: x+y)
    >>> c = OmegaConf.create({
    ...     'key1': '${concat:Hello,World}',
    ...     'key_trimmed': '${concat:Hello , World}',
    ...     'escape_whitespace': '${concat:Hello,\ World}',
    ... })
    >>> c.key1
    'HelloWorld'
    >>> c.key_trimmed
    'HelloWorld'
    >>> c.escape_whitespace
    'Hello World'



Merging configurations
----------------------
Merging configurations enables the creation of reusable configuration files for each logical component
instead of a single config file for each variation of your task.

Machine learning experiment example:

.. code-block:: python

   conf = OmegaConf.merge(base_cfg, model_cfg, optimizer_cfg, dataset_cfg)

Web server configuration example:

.. code-block:: python

   conf = OmegaConf.merge(server_cfg, plugin1_cfg, site1_cfg, site2_cfg)

The following example creates two configs from files, and one from the cli. It then combines them into a single object.
Note how the port changes to 82, and how the users lists are combined.

**example2.yaml** file:

.. include:: example2.yaml
   :code: yaml

**example3.yaml** file:

.. include:: example3.yaml
   :code: yaml


.. doctest::

    >>> from omegaconf import OmegaConf
    >>> import sys
    >>> base_conf = OmegaConf.load('source/example2.yaml')
    >>> second_conf = OmegaConf.load('source/example3.yaml')

    >>> # Merge configs:
    >>> conf = OmegaConf.merge(base_conf, second_conf)

    >>> # Simulate command line arguments
    >>> sys.argv = ['program.py', 'server.port=82']
    >>> # Merge with cli arguments
    >>> conf.merge_with_cli()
    >>> print(conf.pretty())
    log:
      file: log.txt
    server:
      port: 82
    users:
    - user1
    - user2
    <BLANKLINE>

Configuration flags
-------------------

.. note:: Flags are a new feature in 1.3.0 (Pre release). The API is not considered stable yet and might change before 1.3.0 is released.


OmegaConf support several configuration flags.
Configuration flags can be set on any configuration node (Sequence or Mapping). if a configuration flag is not set
it inherits the value from the parent of the node.
The default value inherited from the root node is always false.

Read-only flag
^^^^^^^^^^^^^^
A read-only configuration cannot be modified.
An attempt to modify it will result in omegaconf.ReadonlyConfigError exception

.. doctest:: loaded

    >>> conf = OmegaConf.create(dict(a=dict(b=10)))
    >>> OmegaConf.set_readonly(conf, True)
    >>> conf.a.b = 20
    Traceback (most recent call last):
    ...
    omegaconf.ReadonlyConfigError: a.b

You can temporarily remove the read only flag from a config object:

.. doctest:: loaded

    >>> import omegaconf
    >>> conf = OmegaConf.create(dict(a=dict(b=10)))
    >>> OmegaConf.set_readonly(conf, True)
    >>> with omegaconf.read_write(conf):
    ...   conf.a.b = 20
    >>> conf.a.b
    20

Struct flag
^^^^^^^^^^^
By default, OmegaConf dictionaries allow read and write access to unknown fields.
If a field does not exist, accessing it will return None and writing it will create the field.
It's sometime useful to change this behavior.


.. doctest:: loaded

    >>> conf = OmegaConf.create(dict(a=dict(aa=10, bb=20)))
    >>> OmegaConf.set_struct(conf, True)
    >>> conf.a.cc = 30
    Traceback (most recent call last):
    ...
    KeyError: 'Accessing unknown key in a struct : a.cc'

You can temporarily remove the struct flag from a config object:

.. doctest:: loaded

    >>> import omegaconf
    >>> conf = OmegaConf.create(dict(a=dict(aa=10, bb=20)))
    >>> OmegaConf.set_struct(conf, True)
    >>> with omegaconf.open_dict(conf):
    ...   conf.a.cc = 30
    >>> conf.a.cc
    30

Utility functions
-----------------

OmegaConf.to_container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
OmegaConf config objects looks very similar to python dict and lists, but in fact are not.
Use OmegaConf.to_container(cfg, resolve) to convert to a primitive container.
If resolve is set to True the values will be resolved during conversion.

.. doctest::

    >>> # Simulating command line arguments
    >>> conf = OmegaConf.create({"foo": "bar", "foo2": "${foo}"})
    >>> print(type(conf).__name__)
    DictConfig
    >>> primitive = OmegaConf.to_container(conf)
    >>> print(type(primitive).__name__)
    dict
    >>> print(primitive)
    {'foo': 'bar', 'foo2': '${foo}'}
    >>> resolved = OmegaConf.to_container(conf, resolve=True)
    >>> print(resolved)
    {'foo': 'bar', 'foo2': 'bar'}


OmegaConf.masked_copy
^^^^^^^^^^^^^^^^^^^^^
Creates a copy of a DictConfig that contains only specific keys.
.. doctest:: loaded

    >>> conf = OmegaConf.create(dict(a=dict(b=10), c=20))
    >>> print(conf.pretty())
    a:
      b: 10
    c: 20
    <BLANKLINE>
    >>> c = OmegaConf.masked_copy(conf, ["a"])
    >>> print(c.pretty())
    a:
      b: 10
    <BLANKLINE>

