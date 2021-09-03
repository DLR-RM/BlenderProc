from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

import os
import unittest

loader = unittest.TestLoader()
tests = loader.discover(os.path.dirname(__file__))
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)
