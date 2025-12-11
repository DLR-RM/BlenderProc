from blenderproc.python.utility.SetupUtility import SetupUtility, is_using_external_bpy_module
if not is_using_external_bpy_module():
    SetupUtility.setup([])

import os
import unittest
import blenderproc as bproc

bproc.init()
loader = unittest.TestLoader()
tests = loader.discover(os.path.dirname(__file__))
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)
