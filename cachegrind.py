#!/usr/bin/env python3

# Based on https://github.com/pythonspeed/cachegrind-benchmarking/blob/main/cachegrind.py
"""
Run a program under Cachegrind, combining various metrics into one single performance metric.

License: https://opensource.org/licenses/MIT

## Features

* Disables ASLR.
* Sets consistent cache sizes.
* Calculates a combined performance metric.

For more information see the detailed write up at:

https://pythonspeed.com/articles/consistent-benchmarking-in-ci/

## Usage

$ python3 cachegrind.py ./yourprogram --yourparam=yourvalues

If you're benchmarking Python, make sure to set PYTHONHASHSEED to a fixed value
(e.g. `export PYTHONHASHSEED=1234`).  Other languages may have similar
requirements to reduce variability.

The last line printed will be a combined performance metric, but you can tweak
the script to extract more info, or use it as a library.

Copyright © 2020, Hyphenated Enterprises LLC.
"""

from __future__ import annotations

import sys
import typing as t
from subprocess import DEVNULL
from subprocess import check_call
from subprocess import check_output
from subprocess import run
from tempfile import NamedTemporaryFile


try:
    check_call(['setarch', '-h'], stdout=DEVNULL, stderr=DEVNULL)
    check_call(['valgrind', '-h'], stdout=DEVNULL, stderr=DEVNULL)
except FileNotFoundError as exc:  # e.g. macOS
    raise SystemExit(f'Command not found: {exc.filename}') from None

ARCH = check_output(['uname', '-m'], text=True).strip()
DISABLE_ASLR_CMD = ['setarch', ARCH, '-R']


def run_with_cachegrind(args_list: list[str]) -> dict[str, int]:
    """
    Run the the given program and arguments under Cachegrind, parse the
    Cachegrind specs.

    For now we just ignore program output, and in general this is not robust.
    """
    temp_file = NamedTemporaryFile('r+')
    run([
        *DISABLE_ASLR_CMD,
        'valgrind',
        '--tool=cachegrind',
        # Set some reasonable L1 and LL values, based on Haswell.
        # Feel free to update, important part is that they are consistent across runs,
        # instead of the default of copying from the current machine.
        '--I1=32768,8,64',
        '--D1=32768,8,64',
        '--LL=8388608,16,64',
        '--cachegrind-out-file=' + temp_file.name,
        *args_list,
    ])  # Don't fail if the program fails (to support e.g. `pytest --benchmark-compare-fail=...`)
    return parse_cachegrind_output(temp_file)


def parse_cachegrind_output(temp_file: t.IO[str]) -> dict[str, int]:
    header = summary = ''
    for line in temp_file:
        if line.startswith('events: '):
            header = line[len('events: ') :].strip()
        elif line.startswith('summary: '):
            summary = line[len('summary:') :].strip()
    assert header
    assert summary
    return dict(zip(header.split(), (int(i) for i in summary.split())))


def get_counts(cg_results: dict[str, int]) -> dict[str, int]:
    """
    Given the result of run_with_cachegrind(), figure out the parameters we will use for final
    estimate.

    We pretend there's no L2 since Cachegrind doesn't currently support it.

    Caveats: we're not including time to process instructions, only time to
    access instruction cache(s), so we're assuming time to fetch and run_with_cachegrind
    instruction is the same as time to retrieve data if they're both to L1
    cache.
    """
    result = {}
    d = cg_results

    ram_hits = d['DLmr'] + d['DLmw'] + d['ILmr']

    l3_hits = d['I1mr'] + d['D1mw'] + d['D1mr'] - ram_hits

    total_memory_rw = d['Ir'] + d['Dr'] + d['Dw']
    l1_hits = total_memory_rw - l3_hits - ram_hits
    assert total_memory_rw == l1_hits + l3_hits + ram_hits

    result['l1'] = l1_hits
    result['l3'] = l3_hits
    result['ram'] = ram_hits

    return result


def combined_instruction_estimate(counts: dict[str, int]) -> int:
    """
    Given the result of run_with_cachegrind(), return estimate of total time to run_with_cachegrind.

    Multipliers were determined empirically, but some research suggests they're
    a reasonable approximation for cache time ratios.  L3 is probably too low,
    but then we're not simulating L2...
    """
    return counts['l1'] + (5 * counts['l3']) + (35 * counts['ram'])


def main() -> None:
    results = run_with_cachegrind(sys.argv[1:])
    counts = get_counts(results)
    estimate = combined_instruction_estimate(counts)
    print(f'{"*" * 80}\nCombined instruction estimate: {estimate:,}')  # noqa: T201


if __name__ == '__main__':
    main()
