from collections import defaultdict
from re import compile
import pytest


# bench.name is something like: 'test_init[bidict-1024]'
BENCHNAME_PAT = compile('^([^[]+)\[[^-]+-(\d*)\]$')

@pytest.mark.hookwrapper
def pytest_benchmark_group_stats(config, benchmarks, group_by):
    outcome = yield
    result = defaultdict(list)
    for bench in benchmarks:
        match = BENCHNAME_PAT.match(bench.name)
        test, n = match.group(1), match.group(2)
        result[(test, int(n))].append(bench)
    result = [('%s[%s]' % k, v) for (k, v) in sorted(result.items())]
    outcome.force_result(result)
