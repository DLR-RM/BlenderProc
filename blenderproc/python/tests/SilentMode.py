import os
import sys


class SilentMode(object):
    _global_output = None

    def __init__(self):
        if SilentMode._global_output is None:
            SilentMode._global_output = open(os.devnull, "w")

    def __enter__(self):
        """
        While entering the std out is redirected
        """
        sys.stdout = SilentMode._global_output

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        When leaving the print is reset to the standard output
        """
        sys.stdout = sys.__stdout__
