#!/bin/bash
#
# Copyright 2009-2022 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euxo pipefail

log() {
  echo >&2 " *" "$@"
}

main() {
  if ! type pre-commit || ! type pip-compile; then
    log "Fatal error. Hint: pip install -r requirements/dev.txt"
    exit 1
  fi

  git checkout -b deps main

  cd requirements
  pip-compile -U docs.in && pip-compile -U tests.in && pip-compile -U lint.in && pip-compile -U dev.in
  cd -

  pip install -r requirements/dev.txt

  pre-commit autoupdate
  pre-commit clean

  log "Dev dependencies upgraded."
  log "Run tests via 'tox' or by pushing to the 'deps' branch to ensure everything still works."
}

main
