#!/bin/bash

set -ev

sphinx-build -n -b html -b linkcheck -d docs/_build/doctrees docs docs/_build/html 
