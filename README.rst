Getting Started Pycon
---------------------

.. code-block:: pycon

    >>> import redis
    >>> r = redis.Redis(host='localhost', port=6379, db=0)
    >>> r.set('foo', 'bar')
    True
    >>> r.get('foo')
    'bar'


Getting Started Python
----------------------

.. code-block:: python

    >>> import redis
    >>> r = redis.Redis(host='localhost', port=6379, db=0)
    >>> r.set('foo', 'bar')
    True
    >>> r.get('foo')
    'bar'

Foo bar
-------

Stuff here
