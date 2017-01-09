import pytest
from collections import Counter, OrderedDict, Mapping, defaultdict
from bidict import bidict, frozenbidict, frozenorderedbidict, namedbidict, orderedbidict
from itertools import combinations, product


class dictsubcls(dict):
    pass


class orderedbidictsubcls(orderedbidict):
    pass


items = [('a', 1), ('b', 2)]  # use int values so makes sense with Counter
itemsreversed = list(reversed(items))

bidict_items = bidict(items)
frozenbidict_items = frozenbidict(items)
namedbidict_items = namedbidict('named', 'keys', 'vals')(items)
orderedbidict_items = orderedbidict(items)
orderedbidict_itemsreversed = orderedbidict(itemsreversed)
orderedbidictsubcls_items = orderedbidictsubcls(items)
orderedbidictsubcls_itemsreversed = orderedbidictsubcls(itemsreversed)
frozenorderedbidict_items = frozenorderedbidict(items)
frozenorderedbidict_itemsreversed = frozenorderedbidict(itemsreversed)
bidicts = (
    bidict_items,
    frozenbidict_items,
    namedbidict_items,
    orderedbidict_items,
    orderedbidict_itemsreversed,
    orderedbidictsubcls_items,
    orderedbidictsubcls_itemsreversed,
    frozenorderedbidict_items,
    frozenorderedbidict_itemsreversed,
)

dict_itemsreversed = dict(itemsreversed)
counter_itemsreversed = Counter(dict_itemsreversed)
defaultdict_itemsreversed = defaultdict(lambda x: None, itemsreversed)
dictsubcls_itemsreversed = dictsubcls(itemsreversed)
ordereddict_items = OrderedDict(items)
ordereddict_itemsreversed = OrderedDict(itemsreversed)
empty_dict = {}
not_a_mapping = 42
compare_against = (
    dict_itemsreversed,
    counter_itemsreversed,
    defaultdict_itemsreversed,
    dictsubcls_itemsreversed,
    ordereddict_items,
    ordereddict_itemsreversed,
    empty_dict,
    not_a_mapping,
)


@pytest.mark.parametrize('b, other', product(bidicts, compare_against))
def test_eq(b, other):
    if not isinstance(other, Mapping):
        assert b != other
    elif len(b) != len(other):
        assert b != other
    else:
        assert b == other


orderedbidicts_fwd = (
    orderedbidict_items,
    frozenorderedbidict_items,
    orderedbidictsubcls_items,
)
orderedbidicts_reversed = (
    orderedbidict_itemsreversed,
    frozenorderedbidict_itemsreversed,
    orderedbidictsubcls_itemsreversed,
)
orderedbidicts = orderedbidicts_fwd + orderedbidicts_reversed


@pytest.mark.parametrize('b1, b2', combinations(orderedbidicts, 2))
def test_orderedbidict_eq_order_sensitive(b1, b2):
    b1fwd = b1 in orderedbidicts_fwd
    b2fwd = b2 in orderedbidicts_fwd
    if b1fwd == b2fwd:
        assert b1 == b2
    else:
        assert b1 != b2
