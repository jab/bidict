#!/usr/bin/env python3

# Based on https://github.com/pythonspeed/cachegrind-benchmarking/blob/main/cachegrind.py
"""
Run pytest-benchmark benchmarks under Callgrind, and estimate each one's cost from what it executes.

License: https://opensource.org/licenses/MIT

## Features

* Counts only each benchmark's timed calls: not its setup or teardown, nor pytest itself.
* Disables ASLR.
* Sets consistent cache sizes.
* Combines instruction and cache counts into a single performance metric per benchmark.

For more information on the metric see the detailed write up at:

https://pythonspeed.com/articles/consistent-benchmarking-in-ci/

## Usage

$ ./callgrind.py [--json PATH] pytest -p callgrind --benchmark-timer=callgrind.timer ...

This module is also the pytest plugin that the `-p callgrind` loads, and provides the timer that
`--benchmark-timer=callgrind.timer` selects. Only benchmarks that use benchmark.pedantic() are
supported (see timer() below), and pytest must not distribute them to other processes (e.g. with
pytest-xdist), since only the process that Valgrind starts is measured.

Make sure to set PYTHONHASHSEED to a fixed value (e.g. `export PYTHONHASHSEED=1234`).

Copyright © 2020, Hyphenated Enterprises LLC.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import mmap
import os
import platform
import struct
import subprocess as sp
import sys
import time
import typing as t
from pathlib import Path
from tempfile import TemporaryDirectory


#: Set in the environment of the command that main() runs under Callgrind. The plugin below does
#: nothing without it, so loading it in any other run is harmless.
ACTIVE_ENV_VAR = 'CALLGRIND_PY_ACTIVE'

#: Whether this is the process that main() runs under Callgrind.
ACTIVE = bool(os.environ.get(ACTIVE_ENV_VAR))

# The pytest plugin, which runs in the process being measured.
#
# Callgrind starts with instrumentation off, which runs pytest's startup and collection several
# times faster, and with event collection off (see run_with_callgrind()). pytest_runtestloop()
# switches instrumentation on once the tests start. The timer switches collection on for each round
# of a benchmark's timed calls, and pytest_runtest_teardown() then has Callgrind dump what it
# collected across the rounds, labeled with the benchmark's name. Each switch is a Valgrind client
# request: a special no-op instruction sequence that Valgrind intercepts.

# From callgrind.h: VG_USERREQ_TOOL_BASE('C', 'T') and the requests numbered from it.
_ZERO_STATS = 0x43540001
_TOGGLE_COLLECT = 0x43540002
_DUMP_STATS_AT = 0x43540003
_START_INSTRUMENTATION = 0x43540004

#: Machine code for `size_t request(size_t args[6], size_t default)`, which makes the client request
#: that *args* describes (request code first, then its arguments) and returns Valgrind's reply, or
#: *default* when not running under Valgrind. This is what valgrind.h's
#: VALGRIND_DO_CLIENT_REQUEST_EXPR() compiles to, as a function we can call through ctypes, rather
#: than as a C extension that would need compiling. The four rotations sum to 128, so are no-ops.
_CLIENT_REQUEST_CODE = {
    'x86_64': bytes.fromhex(
        '4889f8'  # mov rax, rdi   ; the request
        '4889f2'  # mov rdx, rsi   ; the default reply
        '48c1c703'  # rol rdi, 3
        '48c1c70d'  # rol rdi, 13
        '48c1c73d'  # rol rdi, 61
        '48c1c733'  # rol rdi, 51
        '4887db'  # xchg rbx, rbx  ; rdx = client_request(rax)
        '4889d0'  # mov rax, rdx
        'c3'  # ret
    ),
    'aarch64': struct.pack(
        '<9I',
        0xAA0003E4,  # mov x4, x0          ; the request
        0xAA0103E3,  # mov x3, x1          ; the default reply
        0x93CC0D8C,  # ror x12, x12, #3
        0x93CC358C,  # ror x12, x12, #13
        0x93CCCD8C,  # ror x12, x12, #51
        0x93CCF58C,  # ror x12, x12, #61
        0xAA0A014A,  # orr x10, x10, x10   ; x3 = client_request(x4)
        0xAA0303E0,  # mov x0, x3
        0xD65F03C0,  # ret
    ),
}


def _make_client_request() -> t.Callable[[int, int], int]:
    try:
        code = _CLIENT_REQUEST_CODE[platform.machine()]
    except KeyError:
        raise RuntimeError(f'callgrind.py does not support {platform.machine()}') from None
    page = mmap.mmap(-1, len(code), prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
    page.write(code)
    func = ctypes.CFUNCTYPE(ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t)(
        ctypes.addressof(ctypes.c_char.from_buffer(page))
    )

    def client_request(request: int, arg: int = 0, _page: mmap.mmap = page) -> int:
        # _page keeps the code mapped: func holds only its address.
        return func((ctypes.c_size_t * 6)(request, arg), 0)

    return client_request


_client_request = _make_client_request() if ACTIVE else None
_timer_calls = 0


def pytest_runtestloop() -> None:
    """Switch Callgrind's instrumentation on, for the rest of the run.

    Not only around each benchmark: Callgrind 3.22's dumps after the first come out corrupted if its
    instrumentation is switched off and on again.
    """
    if _client_request is not None:
        _client_request(_START_INSTRUMENTATION)


def timer() -> float:
    """Return time.perf_counter(), first switching Callgrind's event collection on or off.

    pytest-benchmark calls its timer immediately before and after each round of timed calls, and,
    for a benchmark.pedantic() benchmark, nowhere else. So each round's timed calls are collected.
    """
    global _timer_calls
    if _client_request is not None:
        _client_request(_TOGGLE_COLLECT)
        _timer_calls += 1
    return time.perf_counter()


def pytest_runtest_teardown(item: t.Any) -> None:
    """Dump the events collected in this test's timed calls, if it made any."""
    global _timer_calls
    timer_calls, _timer_calls = _timer_calls, 0
    if _client_request is None or not timer_calls:
        return
    if timer_calls % 2:
        # A timed call raised, leaving collection on. The test fails, so discard what was collected.
        _client_request(_TOGGLE_COLLECT)
        _client_request(_ZERO_STATS)
        return
    label = ctypes.create_string_buffer(item.name.encode())
    _client_request(_DUMP_STATS_AT, ctypes.addressof(label))


# The runner, which runs the command under Callgrind and reads what the plugin had it dump.

DUMP_LABEL_PREFIX = 'desc: Trigger: Client Request: '


def run_with_callgrind(args_list: list[str]) -> tuple[int, dict[str, dict[str, int]]]:
    """Run the given command under Callgrind, and parse the dumps that the plugin requested.

    Return the command's exit status along with each dump's events, by label.
    """
    try:
        sp.check_call(['setarch', '-h'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        sp.check_call(['valgrind', '-h'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    except FileNotFoundError as exc:  # e.g. macOS
        raise SystemExit(f'Command not found: {exc.filename}') from None
    env = dict(os.environ)
    env[ACTIVE_ENV_VAR] = '1'
    # Let the command load this module as a plugin, with `-p callgrind`, wherever it runs from.
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(Path(__file__).resolve().parent), env.get('PYTHONPATH')]))
    with TemporaryDirectory() as out_dir:
        # Don't raise if the command fails, but do return its status so that main() can exit with
        # it. Callers such as the benchmark workflow rely on it to tell a failed benchmark run from a
        # successful one.
        proc = sp.Popen(
            [
                'setarch',
                platform.machine(),
                '-R',  # disable ASLR
                'valgrind',
                '--tool=callgrind',
                '--instr-atstart=no',
                '--collect-atstart=no',
                '--cache-sim=yes',
                # Set some reasonable L1 and LL values, based on Haswell.
                # Feel free to update, important part is that they are consistent across runs,
                # instead of the default of copying from the current machine.
                '--I1=32768,8,64',
                '--D1=32768,8,64',
                '--LL=8388608,16,64',
                # %p is the process ID, so that any forked child's dump goes elsewhere.
                '--callgrind-out-file=' + str(Path(out_dir, 'callgrind.out.%p')),
                *args_list,
            ],
            env=env,
        )
        returncode = proc.wait()
        # Neither setarch nor valgrind forks, so the process ID is the command's. Each dump goes to
        # its own file, numbered after the name for the final dump at exit, which has no events.
        results = {}
        dumps = Path(out_dir).glob(f'callgrind.out.{proc.pid}.*')
        for dump in sorted(dumps, key=lambda path: int(path.suffix[1:])):
            label, events = parse_callgrind_output(dump.read_text(encoding='utf-8'))
            if label in results:
                raise SystemExit(f'Found more than one dump labeled {label!r}')
            results[label] = events
    return returncode, results


def parse_callgrind_output(text: str) -> tuple[str, dict[str, int]]:
    label = header = summary = None
    for line in text.splitlines():
        if line.startswith(DUMP_LABEL_PREFIX):
            label = line[len(DUMP_LABEL_PREFIX) :]
        elif line.startswith('events: '):
            header = line[len('events: ') :].split()
        elif line.startswith('summary: '):
            summary = [int(i) for i in line[len('summary: ') :].split()]
    assert label is not None
    assert header is not None
    assert summary is not None
    # Trailing zeros are left out.
    summary += [0] * (len(header) - len(summary))
    return label, dict(zip(header, summary, strict=True))


def get_counts(cg_results: dict[str, int]) -> dict[str, int]:
    """
    Given the events from a dump, figure out the parameters we will use for final estimate.

    We pretend there's no L2 since Callgrind doesn't currently support it.

    Caveats: we're not including time to process instructions, only time to
    access instruction cache(s), so we're assuming time to fetch and run
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
    Given the result of get_counts(), return estimate of total time to run.

    Multipliers were determined empirically, but some research suggests they're
    a reasonable approximation for cache time ratios.  L3 is probably too low,
    but then we're not simulating L2...
    """
    return counts['l1'] + (5 * counts['l3']) + (35 * counts['ram'])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0].strip())
    parser.add_argument('--json', type=Path, help='also write the results to this file, as JSON')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='the pytest command to run')
    args = parser.parse_args()
    if not args.command:
        parser.error('no command given')
    returncode, results = run_with_callgrind(args.command)
    if not results and returncode == 0:
        # Distinct from the benchmarks failing: this means the plugin never ran, or never timed.
        raise SystemExit('No benchmark was measured. Pass pytest -p callgrind --benchmark-timer=callgrind.timer.')
    # Unlike the wall-clock figures pytest-benchmark records, which vary with whatever else is running
    # on the machine, these count instructions and so are reproducible. Record them when asked, so a
    # caller can compare them between revisions.
    records = {
        label: {'estimate': combined_instruction_estimate(get_counts(events)), **events}
        for label, events in results.items()
    }
    width = max(map(len, records), default=0)
    print('*' * 80)
    print("Instructions executed by each benchmark's timed calls, and their combined estimate:")
    for label, record in records.items():
        print(f'{label:<{width}}  {record["Ir"]:>16,}  {record["estimate"]:>16,}')
    totals = (sum(r['Ir'] for r in records.values()), sum(r['estimate'] for r in records.values()))
    print(f'{"Total":<{width}}  {totals[0]:>16,}  {totals[1]:>16,}')
    if args.json:
        args.json.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    sys.exit(returncode)


if __name__ == '__main__':
    main()
