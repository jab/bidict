#!/bin/bash
# this is what .travis.yml and tox.ini use to run tests

set -ev

COV="--cov=bidict"
# With hypothesis>=1.19.0,
# data generation is so slow when using --cov
# that it can cause health checks to fail
# in slow environments such as Travis-CI
# with certain Python versions such as pypy.
# Don't pass --cov in these cases:
[[ $TRAVIS_PYTHON_VERSION =~ ^(pypy)$ ]] && COV=""
py.test $COV || FAILED=1
pep257 bidict || FAILED=1
exit $FAILED
