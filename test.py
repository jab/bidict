# based on https://docs.python.org/3/library/doctest.html#unittest-api

import bidict
import doctest
import unittest

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(bidict))
    return tests
