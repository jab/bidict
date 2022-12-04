#!/usr/bin/env bash
#
# Copyright 2009-2022 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euo pipefail

log() {
  >&2 echo -e "$@"
}

main() {
  if ! type pre-commit || ! type pip-compile; then
    log "Error: pre-commit or pip-compile not found."
    exit 1
  fi

  local -r gitbranch=$(git branch --show-current)
  if [ "$gitbranch" = "deps" ]; then
    log "Already on branch 'deps'"
  elif [ "$gitbranch" = "main" ]; then
    git checkout -b deps main
  else
    log "On unsupported branch '$gitbranch'. Switch to 'main' and try again."
    exit 1
  fi

  # Not adding --generate-hashes due to https://github.com/jazzband/pip-tools/issues/1326
  local -r pip_compile="pip-compile pyproject.toml --upgrade --resolver=backtracking --allow-unsafe"
  ${pip_compile} --extra=test -o dev-deps/test.txt
  ${pip_compile} --extra=docs -o dev-deps/docs.txt
  ${pip_compile} --extra=lint -o dev-deps/lint.txt
  ${pip_compile} --extra=dev -o dev-deps/dev.txt
  pip install -U -r dev-deps/test.txt -r dev-deps/docs.txt -r dev-deps/lint.txt -r dev-deps/dev.txt

  pre-commit autoupdate
  pre-commit clean

  log "Dev dependencies upgraded."
  log "Reminders:" \
    "\n - Check release notes of upgraded packages for anything that affects bidict." \
    "\n - Run tests via 'tox' or by pushing to the 'deps' branch to ensure everything still works." \
    "\n - Check output for any new warnings, not just test failures."
}

main
