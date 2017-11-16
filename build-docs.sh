#!/bin/bash

GRAPH_SRC="type-hierarchy.txt"
MODIFIED_GRAPH_SRC="$(git ls-files -m | grep ${GRAPH_SRC})"

if [[ -n "${MODIFIED_GRAPH_SRC}" ]]; then
  if which graph-easy &>/dev/null ; then
    graph-easy "${MODIFIED_GRAPH_SRC}" --png
    if [[ "$?" -eq 0 ]]; then
      if which optipng &>/dev/null ; then
        optipng _static/type-hierarchy.png
      else
        echo -e "\033[0;31m* optipng not found, skipping. Hint: brew install optipng\033[0m\0007"
      fi
    else
      echo -e "\033[0;31m* graph-easy failed. Hint: brew install graphviz\033[0m\0007"
    fi
  else
    echo -e "\033[0;31m* graph-easy not found, skipping. Hint: sudo cpanm Graph::Easy\033[0m\0007"
  fi
fi

cd docs
make clean html $@
