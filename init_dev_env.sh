#!/bin/bash

set -euo pipefail

pre-commit install -f

if ! test -d .venv; then
  mkdir .venv
fi
if ! test -d .venv/dev; then
  python3.11 -m venv --upgrade-deps .venv/dev
fi

# shellcheck disable=SC1091
source .venv/dev/bin/activate
type -p pip-sync || pip install pip-tools
pip-sync dev-deps/python3.11/dev.txt dev-deps/python3.11/test.txt
pip show -qq bidict || pip install -e .
