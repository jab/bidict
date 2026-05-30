#!/usr/bin/env bash
#
# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euo pipefail

declare -r container_image='rust:1.95-bookworm'

if ! command -v container >/dev/null 2>&1; then
  >&2 echo "Error: No 'container' command on PATH."
  exit 1
fi

repo_root=$(
  cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
  pwd
)

# shellcheck disable=SC2016
container run --rm --progress plain \
  -v "${repo_root}:/work" \
  -w /work \
  "${container_image}" \
  bash -c '
    set -euo pipefail
    if [ -n "${1:-}" ]; then
      export BIDICT_DISABLE_NATIVE="$1"
    fi
    export DEBIAN_FRONTEND=noninteractive
    export PYTHONHASHSEED=42
    export UV_LINK_MODE=copy
    export UV_PROJECT_ENVIRONMENT=/tmp/bidict-bench-venv

    apt-get update >/dev/null
    apt-get install -y \
      build-essential \
      ca-certificates \
      python3 \
      python3-dev \
      python3-pip \
      python3-venv \
      util-linux \
      valgrind \
      >/dev/null
    python3 -m pip install --break-system-packages uv >/dev/null

    rustc --version
    cargo --version

    uv sync --all-groups --frozen >/dev/null
    . /tmp/bidict-bench-venv/bin/activate

    python - <<"PY"
import os

import bidict._native as native

disabled = os.getenv("BIDICT_DISABLE_NATIVE")
if disabled:
    assert native.build_bidict_maps is None and native.update_bidict_maps is None
    print(f"native helper: disabled via BIDICT_DISABLE_NATIVE={disabled}")
else:
    assert native.build_bidict_maps is not None
    print("native helper:", native.build_bidict_maps.__module__)
PY

    ./cachegrind.py python -m pytest -c /dev/null -n0 \
      --benchmark-columns=min,rounds,iterations \
      --benchmark-disable-gc \
      --benchmark-group-by=name \
      microbenchmarks.py
  ' bash "${BIDICT_DISABLE_NATIVE-}"
