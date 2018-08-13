#!/bin/bash
#
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


LAST_EXIT="0"

# Generate a new types diagram image from the source file if it's been modified
GRAPH_SRC="bidict-types-diagram.dot"
MODIFIED_GRAPH_SRC="$(git ls-files -m | grep ${GRAPH_SRC})"

if [[ -n "${MODIFIED_GRAPH_SRC}" ]]; then
  MODIFIED_GRAPH_DST="${MODIFIED_GRAPH_SRC%.*}.png"
  if which dot &>/dev/null ; then
    dot -v -Tpng -o "${MODIFIED_GRAPH_DST}" < "${MODIFIED_GRAPH_SRC}"
    LAST_EXIT="$?"
    if [[ "${LAST_EXIT}" -ne 0 ]]; then
      echo -e "\033[0;31m* dot exited nonzero (${LAST_EXIT})\033[0m\0007"
    else
      if which optipng &>/dev/null ; then
        optipng "${MODIFIED_GRAPH_DST}"
        LAST_EXIT="$?"
        if [[ "LAST_EXIT" -ne 0 ]]; then
          echo -e "\033[0;31m* optipng exited nonzero (${LAST_EXIT})\033[0m\0007"
        fi
      else
        echo -e "\033[0;31m* optipng not found, skipping. Hint: brew install optipng\033[0m\0007"
      fi
    fi
  else
    echo -e "\033[0;31m* dot not found, skipping. Hint: brew install graphviz\033[0m\0007"
  fi
fi


# Build the docs.
cd docs
make clean html
