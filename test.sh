#!/bin/bash
# this is what .travis.yml and tox.ini use to run tests

set -ev
test -z "$BIDICT_COVERAGE_DISABLE" && COV="--cov=bidict"
py.test $COV || EXIT=1
flake8 bidict || EXIT=1
pydocstyle bidict || EXIT=1
exit $EXIT
