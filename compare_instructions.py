#!/usr/bin/env python3
# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Compare two sets of per-benchmark instruction estimates recorded by `./callgrind.py --json`.

Prints a Markdown report of the benchmarks whose estimate changed by more than --threshold percent,
in either direction, and of the change in their total, followed by a table of every benchmark.
With --github-output, also appends `state` (regression, improved, or ok) and a one-line `summary`
to that file, in the form that GitHub Actions expects of $GITHUB_OUTPUT.
"""

from __future__ import annotations

import argparse
import json
import typing as t
from pathlib import Path


class Change(t.NamedTuple):
    name: str
    baseline: int
    current: int

    @property
    def pct(self) -> float:
        return (self.current - self.baseline) / self.baseline * 100


def load(path: Path) -> dict[str, int]:
    return {name: result['estimate'] for name, result in json.loads(path.read_text(encoding='utf-8')).items()}


def fmt_pct(pct: float) -> str:
    return f'{pct:+.2f}%'


def table(changes: t.Iterable[Change]) -> list[str]:
    rows = ['| Benchmark | Baseline | This revision | Change |', '| :-- | --: | --: | --: |']
    rows.extend(f'| `{c.name}` | {c.baseline:,} | {c.current:,} | {fmt_pct(c.pct)} |' for c in changes)
    return rows


def compare(
    baseline: dict[str, int], current: dict[str, int], threshold: float, total_threshold: float
) -> tuple[str, str, str]:
    """Return the state, a one-line summary, and a Markdown report."""
    changes = [Change(name, baseline[name], estimate) for name, estimate in current.items() if name in baseline]
    regressed = sorted((c for c in changes if c.pct > threshold), key=lambda c: -c.pct)
    improved = sorted((c for c in changes if c.pct < -threshold), key=lambda c: c.pct)
    # Only benchmarks in both runs count toward the total, so that adding or removing one does not
    # register as a change in the others.
    total = Change('total', sum(c.baseline for c in changes), sum(c.current for c in changes))
    if regressed or total.pct > total_threshold:
        state = 'regression'
    elif improved or total.pct < -total_threshold:
        state = 'improved'
    else:
        state = 'ok'
    n = len(changes)
    if regressed:
        summary = f'{len(regressed)} of {n} benchmarks regressed by more than {threshold}%'
        if improved:
            summary += f', and {len(improved)} improved'
    elif improved:
        summary = f'{len(improved)} of {n} benchmarks improved by more than {threshold}%'
    else:
        summary = f'none of {n} benchmarks changed by more than {threshold}%'
    summary += f'; their total changed by {fmt_pct(total.pct)}'
    if abs(total.pct) > total_threshold:
        summary += f', more than {total_threshold}%'

    report = []
    if regressed or improved:
        report += [*table(regressed + improved), '']
    total_change = f'{total.baseline:,} → {total.current:,} ({fmt_pct(total.pct)})'
    report.append(f'Total of the {n} benchmarks in both runs: {total_change}.')
    if added := [name for name in current if name not in baseline]:
        report += ['', 'New, so not compared: ' + ', '.join(f'`{name}`' for name in added) + '.']
    if removed := [name for name in baseline if name not in current]:
        report += ['', 'In the baseline but not run: ' + ', '.join(f'`{name}`' for name in removed) + '.']
    report += ['', '<details><summary>All benchmarks</summary>', '', *table(changes), '', '</details>']
    return state, summary, '\n'.join(report) + '\n'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('baseline', type=Path)
    parser.add_argument('current', type=Path)
    parser.add_argument('--threshold', type=float, required=True, help='percent change in a benchmark to report')
    parser.add_argument('--total-threshold', type=float, required=True, help='percent change in the total to report')
    parser.add_argument('--github-output', type=Path, help='file to append state and summary to')
    args = parser.parse_args()
    state, summary, report = compare(load(args.baseline), load(args.current), args.threshold, args.total_threshold)
    print(report, end='')
    if args.github_output:
        with args.github_output.open('a', encoding='utf-8') as f:
            f.write(f'state={state}\nsummary={summary}\n')


if __name__ == '__main__':
    main()
