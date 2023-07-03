#!/usr/bin/env bash
#
# Copyright 2009-2023 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# shellcheck disable=SC2086


set -euo pipefail

log() {
  >&2 printf "> %s\n" "$@"
}


main() {
  local -r gitbranch=$(git branch --show-current)
  if [ "$gitbranch" = "deps" ] || [ "$gitbranch" = "dev" ]; then
    log "Already on branch '$gitbranch'"
  elif [ "$gitbranch" = "main" ]; then
    git checkout -b deps main
  else
    log "On unsupported branch '$gitbranch'. Switch to 'main' and try again."
    exit 1
  fi


  # In case pypy38 only provides a "pypy3" executable, not a "pypy3.8",
  # expect a PYPY38 env var pointing to a pypy3.8, as exported by flake.nix:
  if ! type pypy3.8 &>/dev/null; then
    function pypy3.8 {
      $PYPY38 "$@"
    }
  fi

  log "Upgrading PyPI dependencies..."
  local -r dev_py="python3.11"  # Main version used for development
  local -r pip_compile="pip-compile --generate-hashes --reuse-hashes --upgrade --resolver=backtracking --allow-unsafe"
  for py in python3.12 python3.11 python3.10 python3.9 python3.8 pypy3.9 pypy3.8; do
    local manage_deps_env=".venv/deps/$py"
    [ -e "$manage_deps_env" ] || $py -m venv "$manage_deps_env"
    "$manage_deps_env/bin/pip" install --upgrade pip
    "$manage_deps_env/bin/pip" install --upgrade pip-tools
    mkdir -pv "dev-deps/$py"
    $manage_deps_env/bin/$pip_compile dev-deps/test.in -o "dev-deps/$py/test.txt" >/dev/null
    # Compile remaining layers just for our dev interpreter (3.11):
    if [ "$py" = "$dev_py" ]; then
      for i in docs lint dev; do
        $manage_deps_env/bin/$pip_compile "dev-deps/$i.in" -o "dev-deps/$py/$i.txt"
      done
    fi
  done
  .venv/dev/bin/pip install --upgrade pip-tools
  .venv/dev/bin/pip-sync dev-deps/$dev_py/{docs,lint,test,dev}.txt
  .venv/dev/bin/pip install -e .
  log "Upgrading PyPI dependencies: Done"

  log "Upgrading pre-commit hooks..."
  .venv/dev/bin/pre-commit autoupdate
  log "Upgrading pre-commit hooks: Testing..."
  git add .
  .venv/dev/bin/pre-commit run --all-files

  log "Done."
  log "Reminders:"
  log " - Check release notes of upgraded packages for anything that affects bidict."
  log " - Run tests via 'tox' or by pushing to the 'deps' branch to ensure everything still works."
  log " - Check output for any new warnings, not just test failures."
}

main
