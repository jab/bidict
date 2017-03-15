"""
Test that if foreign code provides a class that conforms to
BidirectionalMapping's interface, it is automatically a subclass.
"""
from bidict import BidirectionalMapping
from bidict.compat import PY2


class DumbBidirectionalMapping(dict):
    def __inverted__(self):
        for (key, val) in self.items():
            yield (val, key)

    @property
    def inv(self):
        return DumbBidirectionalMapping(self.__inverted__())


if PY2:
    class OldStyleClass:
        """Old-style class (not derived from object)."""


def test_subclasshook():
    assert issubclass(DumbBidirectionalMapping, BidirectionalMapping)
    assert not issubclass(dict, BidirectionalMapping)
    if PY2:  # Make sure this works with old-style classes as expected.
        assert not issubclass(OldStyleClass, BidirectionalMapping)
