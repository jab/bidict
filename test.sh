#!/bin/bash
# this is what .travis.yml and tox.ini use to run tests

set -ev

# on python2 and hypothesis>=1.19.0,
# hypothesis data generation is so slow when using --cov
# that it causes health checks to fail,
# so only pass --cov when on python3:
python -c 'import sys; exit(sys.version_info.major == 2)' && COV="--cov=bidict"
py.test $COV || FAILED=1
pep257 bidict || FAILED=1
exit $FAILED
