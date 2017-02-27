import bidict, sortedcontainers, sortedcollections, collections

class sortedbidict2(bidict.OrderedMapping, bidict.bidict):
    _fwd_class = sortedcontainers.SortedDict
_inv_class = sortedcollections.ValueSortedDict

elemByAtomicNum = sortedbidict2({1: 'hydrogen', 2: 'helium', 3: 'lithium'})

elemByAtomicNum.update({4: 'beryllium'})

# order is preserved correctly when passing .inv back into constructor:
atomicNumByElem = sortedbidict2(elemByAtomicNum.inv)

# attrs not defined by bidict are passed through to the _fwd SortedDict:
elemByAtomicNum.peekitem(index=0)
elemByAtomicNum.popitem(last=False)
elemByAtomicNum.inv.popitem(last=True)

elemByAtomicNum == {2: 'helium', 3: 'lithium'}
elemByAtomicNum == {3: 'lithium', 2: 'helium'}
bidict.OrderedMapping.__eq__(elemByAtomicNum, {3: 'lithium', 2: 'helium'})
collections.Mapping.__eq__(elemByAtomicNum, {3: 'lithium', 2: 'helium'})
