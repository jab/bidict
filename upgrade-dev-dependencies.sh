#!/bin/bash
#
# Copyright 2009-2022 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euo pipefail

log() {
  echo -e >&2 "$@"
}

main() {
  if ! type pre-commit || ! type pip-compile-multi; then
    log "Error: pre-commit or pip-compile-multi not found." \
      "\n       Hint: pip install -r requirements/dev.txt"
    exit 1
  fi

  git checkout -b deps main

  pip-compile-multi
  pip install -r requirements/dev.txt

  pre-commit autoupdate
  pre-commit clean

  log "Dev dependencies upgraded."
  log "Reminders:" \
    "\n - Check release notes of upgraded packages for anything that affects bidict." \
    "\n - Run tests via 'tox' or by pushing to the 'deps' branch to ensure everything still works." \
    "\n - Check output for any new warnings, not just test failures."
}

main
