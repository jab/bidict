#!/bin/bash
# this is what .travis.yml and tox.ini use to run tests

set -ev

flake8 bidict tests/*.py || { EXIT=1 && echo -e "\033[0;31m * flake8 failed \033[0m \0007"; }
pydocstyle bidict || { EXIT=1 && echo -e "\033[0;31m * pydocstyle failed \033[0m \0007"; }
test -z "$BIDICT_BUILD_DOCS_ENABLE" || { ./build-docs.sh || { EXIT=1 && echo -e "\033[0;31m * build-docs.sh failed \033[0m \0007"; } ; }

test -z "$BIDICT_COVERAGE_ENABLE" || COV="--cov=bidict --cov-branch"
test -z "$BENCHMARK_DIR" || BENCHMARK_STORAGE="--benchmark-storage=$BENCHMARK_DIR"
py.test $COV $BENCHMARK_STORAGE $BENCHMARK_SKIP || { EXIT=1 && echo -e "\033[0;31m * pytest failed \033[0m \0007"; }

exit $EXIT
