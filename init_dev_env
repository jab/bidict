#!/bin/bash

set -euo pipefail

if ! type python3.11; then
  >&2 echo "No python3.11 on PATH. Hint: Use direnv + ./flake.nix to bootstrap a development environment"
  exit 1
fi

if ! test -d .venv; then
  mkdir .venv
fi
if ! test -d .venv/dev; then
  python3.11 -m venv --upgrade-deps .venv/dev
fi

if type pre-commit; then
  pre-commit install -f
else
  >&2 echo "No pre-commit on PATH. Hint: Use direnv + ./flake.nix to bootstrap a development environment"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/dev/bin/activate
type -p pip-sync || pip install pip-tools
pip-sync dev-deps/python3.11/dev.txt dev-deps/python3.11/test.txt
pip show -qq bidict || pip install -e .
