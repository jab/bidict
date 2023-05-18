#!/usr/bin/env bash
#
# Copyright 2009-2023 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euo pipefail

log() {
  >&2 printf "> %s\n" "$@"
}

main() {
  if ! type pre-commit || ! type pip-compile; then
    log "Error: pre-commit or pip-compile not found."
    exit 1
  fi
  if [ -z "$VIRTUAL_ENV" ]; then
    log "Error: Activate a development virtualenv and try again."
    exit 2
  fi

  local -r gitbranch=$(git branch --show-current)
  if [ "$gitbranch" = "deps" ] || [ "$gitbranch" = "dev" ]; then
    log "Already on branch '$gitbranch'"
  elif [ "$gitbranch" = "main" ]; then
    git checkout -b deps main
  else
    log "On unsupported branch '$gitbranch'. Switch to 'main' and try again."
    exit 1
  fi

  log "Upgrading PyPI dependencies..."
  # Not adding --generate-hashes due to https://github.com/jazzband/pip-tools/issues/1326
  local -r pip_compile="pip-compile --upgrade --resolver=backtracking --allow-unsafe"
  # Compile dev.in last since it includes the others:
  for i in dev-deps/{lint,docs,test,dev}.in; do
    $pip_compile "$i" -o "${i/%in/txt}"
  done
  pip-sync dev-deps/dev.txt
  log "Upgrading PyPI dependencies: Done"

  log "Upgrading pre-commit hooks..."
  pre-commit autoupdate
  log "Upgrading pre-commit hooks: Testing..."
  git add .
  pre-commit run --all-files

  log "Done."
  log "Reminders:"
  log " - Check release notes of upgraded packages for anything that affects bidict."
  log " - Run tests via 'tox' or by pushing to the 'deps' branch to ensure everything still works."
  log " - Check output for any new warnings, not just test failures."
}

main
