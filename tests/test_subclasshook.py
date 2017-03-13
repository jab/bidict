"""
Test that if foreign code provides a class that conforms to
BidirectionalMapping's interface, it is automatically a subclass.
"""
from bidict import BidirectionalMapping


class DumbBidirectionalMapping(dict):
    def __inverted__(self):
        for (key, val) in self.items():
            yield (val, key)

    @property
    def inv(self):
        return DumbBidirectionalMapping(self.__inverted__())


class OldstyleClass():
    """
    Old-style class (not derived from object).
    This used to crash due to missing __mro__ attribute that is not present
    in oldstyle classes.
    """


def test_subclasshook():
    assert issubclass(DumbBidirectionalMapping, BidirectionalMapping)
    assert not issubclass(dict, BidirectionalMapping)
    assert not issubclass(OldstyleClass, BidirectionalMapping)
