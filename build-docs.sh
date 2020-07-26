#!/bin/bash
#
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

set -euo pipefail

log() {
  echo >&2 " *" "$@"
}

# Generate a new graph image from its source file if it's been modified.
update_graph() {
  local -r graph_src="bidict-types-diagram.dot"
  local -r graph_dst="${graph_src%.*}.png"

  if [[ ! "$(git diff --name-only -- "$graph_src")" ]] &&
    [[ ! "$(git diff --name-only --cached -- "$graph_src")" ]]; then
    log "$graph_src not modified -> skipping graph update."
    return 0
  fi

  if ! command -v dot &>/dev/null; then
    log "'dot' not found -> skipping graph update. Hint: brew install graphviz"
    return 1
  fi

  if ! dot -v -Tpng -o "$graph_dst" <"$graph_src"; then
    log "dot exited nonzero."
    return 1
  fi

  # return 0 if any of the below fail because running dot succeeded, which is the main thing.
  if ! command -v optipng &>/dev/null; then
    log "'optipng' not found -> skipping png optimization. Hint: brew install optipng"
    return 0
  fi

  if ! optipng "$graph_dst"; then
    log "optipng exited nonzero."
    return 0
  fi
}

# Use parentheses instead of braces around body so it runs in a subshell -> cd doesn't leak.
build_docs() (
  make clean html
)

main() {
  cd assets
    update_graph
  cd -
  cd docs
    build_docs
  cd -
}

main
