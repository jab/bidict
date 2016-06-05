#!/bin/bash
# this is what .travis.yml and tox.ini use to run tests

set -ev

flake8 bidict tests/*.py || EXIT=1
pydocstyle bidict || EXIT=1

test -z "$BIDICT_COVERAGE_DISABLE" && COV="--cov=bidict"
test -n "$BENCHMARK_DIR" && BENCHMARK_STORAGE="--benchmark-storage=$BENCHMARK_DIR"
py.test $COV $BENCHMARK_STORAGE || EXIT=1

exit $EXIT
