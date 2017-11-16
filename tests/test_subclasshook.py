"""
Test that if foreign code provides a class that conforms to
BidirectionalMapping's interface, it is automatically a subclass.
"""
from bidict import BidirectionalMapping
from bidict.compat import PY2


class DumbBidirectionalMapping(dict):
    """Dummy type implementing the BidirectionalMapping interface."""
    def __inverted__(self):
        for (key, val) in self.items():
            yield (val, key)

    @property
    def inv(self):
        """Like :attr:`bidict.bidict.inv`."""
        return DumbBidirectionalMapping(self.__inverted__())


if PY2:
    class OldStyleClass:
        """Old-style class (not derived from object)."""


def test_subclasshook():
    """Ensure issubclass works as expected."""
    assert issubclass(DumbBidirectionalMapping, BidirectionalMapping)
    assert not issubclass(dict, BidirectionalMapping)
    if PY2:  # Make sure this works with old-style classes as expected.
        assert not issubclass(OldStyleClass, BidirectionalMapping)
