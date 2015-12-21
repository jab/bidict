nan As Key
^^^^^^^^^^

`In CPython <http://doc.pypy.org/en/latest/cpython_differences.html>`_,
nan is especially tricky when used as a dictionary key::

    >>> d = {float('nan'): 'nan'}
    >>> d
    {nan: 'nan'}
    >>> d[float('nan')]  # doctest: +SKIP
    Traceback (most recent call last):
        ...
    KeyError: nan
    >>> d[float('nan')] = 'not overwritten'
    >>> d  # doctest: +SKIP
    {nan: 'nan', nan: 'not overwritten'}

In other Python implementations such as PyPy,
nan behaves just like any other dictionary key.
But in CPython, beware of this unexpected behavior.
