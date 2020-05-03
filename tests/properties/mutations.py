import pytest_mutagen as mg

from bidict._base import BidictBase
from bidict._mut import MutableBidict
from bidict._orderedbase import OrderedBidictBase

mg.link_to_file("**all**")

# BidictBase

@mg.mutant_of("BidictBase._isinv", "IS_INV_INVERTED")
def _isinv_inverted(self):
    return not self._inv is None


@mg.mutant_of("BidictBase._already_have", "ALREADY_HAVE_TRUE_BIDICTBASE", description="_already_have always returns true")
def _already_have_true(key, val, oldkey, oldval):
    return True

# OrderedBidict

@mg.mutant_of("OrderedBidictBase._already_have", "ALREADY_HAVE_TRUE_ORDEREDBIDICTBASE", description="_already_have always returns true")
def _already_have_true(key, val, oldkey, oldval):
    return True


# MutableBidict

from bidict._dup import ON_DUP_RAISE
@mg.mutant_of("MutableBidict.put", "PUT_NOTHING")
def put_nothing(self, key, val, on_dup=ON_DUP_RAISE):
    pass

@mg.mutant_of("MutableBidict.putall", "PUT_NOTHING")
def putall_nothing(self, items, on_dup=ON_DUP_RAISE):
    pass

@mg.mutant_of("MutableBidict.clear", "CLEAR_NOTHING")
def mutable_clear_nothing(self):
    pass

@mg.mutant_of("OrderedBidict.clear", "CLEAR_NOTHING")
def ordered_clear_nothing(self):
    pass

@mg.mutant_of("MutableBidict.update", "UPDATE_NOTHING")
def update_nothing(self, *args, **kw):
    pass

@mg.mutant_of("MutableBidict.__delitem__", "__DELITEM__NOTHING")
def __delitem__nothing(self, key):
    if self.__getitem__(key):
        return
    raise KeyError
