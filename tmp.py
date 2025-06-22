import bidict as b


f = b.BidictBase({1: 'one'})

reveal_type(f)
reveal_type(f.inverse)
