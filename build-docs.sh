#!/bin/bash

GRAPH_SRC="bidict-types-diagram.dot"
MODIFIED_GRAPH_SRC="$(git ls-files -m | grep ${GRAPH_SRC})"

if [[ -n "${MODIFIED_GRAPH_SRC}" ]]; then
  MODIFIED_GRAPH_DST="${MODIFIED_GRAPH_SRC%.*}.png"
  if which dot &>/dev/null ; then
    dot -v -Tpng < "${MODIFIED_GRAPH_SRC}" > "${MODIFIED_GRAPH_DST}"
    if [[ "$?" -eq 0 ]]; then
      if which optipng &>/dev/null ; then
        optipng "{MODIFIED_GRAPH_DST}"
      else
        echo -e "\033[0;31m* optipng not found, skipping. Hint: brew install optipng\033[0m\0007"
      fi
    else
      echo -e "\033[0;31m* dot exited nonzero ($?)\033[0m\0007"
    fi
  else
    echo -e "\033[0;31m* dot not found, skipping. Hint: brew install graphviz\033[0m\0007"
  fi
fi

cd docs
make clean html $@
