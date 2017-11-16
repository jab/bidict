"""
Test :attr:`bidict.__version__`.
"""

import bidict


def test_version():
    """Ensure the module has a ``__version__`` attribute."""
    assert bidict.__version__
