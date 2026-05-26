#!/usr/bin/env bash
#
# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euo pipefail

if ! command -v container >/dev/null 2>&1; then
  >&2 echo "Error: No 'container' command on PATH."
  exit 1
fi

repo_root=$(
  cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
  pwd
)

container run --rm --progress plain \
  -v "${repo_root}:/work" \
  -w /work \
  ubuntu:24.04 \
  bash -lc '
    set -euo pipefail
    export DEBIAN_FRONTEND=noninteractive
    export PYTHONHASHSEED=42
    export UV_LINK_MODE=copy
    export UV_PROJECT_ENVIRONMENT=/tmp/bidict-bench-venv

    apt-get update >/dev/null
    apt-get install -y ca-certificates git util-linux valgrind python3 python3-venv python3-pip >/dev/null
    python3 -m pip install --break-system-packages uv >/dev/null

    uv sync --only-group test >/dev/null
    . /tmp/bidict-bench-venv/bin/activate

    ./cachegrind.py python -m pytest -c /dev/null -n0 \
      --benchmark-columns=min,rounds,iterations \
      --benchmark-disable-gc \
      --benchmark-group-by=name \
      microbenchmarks.py
  '
