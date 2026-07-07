# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

`bidict` is a mature, dependency-free bidirectional mapping library
for Python (>=3.11, CPython + PyPy).
The public API is small;
the value is in the carefully-factored, fully type-hinted implementation.
Optimize for correctness, API stability, and long-term maintainability
over cleverness.
There are **zero runtime dependencies** (standard library only) —
do not add any.

## Canonical docs (imported so their content is in-session)

These human-facing docs are the single source of truth.
When the underlying facts change,
update *them* rather than duplicating anything here:

- Contributor workflow —
  dev environment, running tests and checks, single-test invocation,
  the property-based (Hypothesis) testing approach,
  code style and lint, commit conventions,
  the Semantic Line Breaks prose convention,
  and the fact that doctests in modules and `docs/*.rst` run as tests:
  @CONTRIBUTING.rst
- Architecture, code structure,
  and the guided "code review nav" reading order through the source:
  @docs/learning-from-bidict.rst
- Extending bidict —
  custom subclasses, `on_dup` policies, dynamic inverse-class generation:
  @docs/extending.rst

## Working in this codebase (Claude-specific notes)

- Run dev tooling through the Nix dev shell, not the bare `.venv`:
  prefix commands with `nix develop --command bash -c '...'`
  (or work from within a `nix develop` shell).
  `prek`, `tox`, and the docs build are provided only by the Nix shell,
  so invoking them outside it fails with "command not found" —
  even though `pytest` and `mypy` happen to also be in `.venv`,
  which makes it easy to forget.
  The committed `.envrc` (`use flake`) does not help here,
  because direnv has no hook in the non-interactive subshells
  spawned for these tool calls.
- SemBr ([Semantic Line Breaks](https://sembr.org), see CONTRIBUTING.rst)
  applies to prose in Markdown and reStructuredText documents only
  (this file, `CONTRIBUTING.rst`, `docs/*.rst`):
  one sentence per line, breaking at clause boundaries,
  don't reflow paragraphs to fill columns.
  It does *not* apply to code, code comments, docstrings, or commit messages.
- Follow the "Code review nav" banner comments
  at the top and bottom of each key file
  (start in `bidict/__init__.py`);
  they define the author's intended reading order.
  `_base.py`'s `BidictBase` is the heart of the library.
- `_base.py` holds the subtle machinery,
  each piece explained in inline comments —
  **read those comments before editing** the relevant code.
  The landmarks to be careful around:
  - a bidict and its `.inverse` **share** the same two backing dicts
    (`_fwdm`/`_invm`, swapped),
    so mutations through either are visible in both;
  - the `inverse` property's strong-ref/weakref pair,
    which exposes the inverse without creating a reference cycle;
  - `_ensure_inv_cls`/`_make_inv_cls`,
    which synthesize a distinct inverse class
    when the forward and inverse backing types differ
    (intentionally corecursive with `__init_subclass__`);
  - the `_dedup` → `_write` mutation path,
    which records "unwrites"
    so a failing bulk `_update` rolls back atomically.
- Every source file carries the MPL-2.0 header —
  include it on new files.
  Public API changes must be reflected in `CHANGELOG.rst`
  and the relevant `docs/*.rst`.
