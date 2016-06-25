#!/bin/bash
# this is what .travis.yml and tox.ini use to run tests

set -ev

flake8 bidict tests/*.py || { EXIT=1 && echo -e "\0007flake8 failed"; }
pydocstyle bidict || { EXIT=1 && echo -e "\0007pydocstyle failed"; }
test -z "$BIDICT_SPHINXBUILD_DISABLE" && { sphinx-build -n -b html -b linkcheck -d docs/_build/doctrees docs docs/_build/html || { EXIT=1 && echo -e "\0007docsbuild failed"; } ;}

test -z "$BIDICT_COVERAGE_DISABLE" && COV="--cov=bidict"
test -n "$BENCHMARK_DIR" && BENCHMARK_STORAGE="--benchmark-storage=$BENCHMARK_DIR"
py.test $COV $BENCHMARK_STORAGE || { EXIT=1 && echo -e "\0007pytest failed"; }

exit $EXIT
