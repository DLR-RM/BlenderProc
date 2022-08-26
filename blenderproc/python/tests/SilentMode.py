""" Allows to redirect the std out to avoid any output """

import os
import sys


class SilentMode:
    """ Allows to redirect the std out to avoid any output """

    _global_output = None

    def __init__(self):
        if SilentMode._global_output is None:
            #pylint: disable=consider-using-with
            SilentMode._global_output = open(os.devnull, "w", encoding="utf-8")
            #pylint: enable=consider-using-with


    def __del__(self):
        if SilentMode._global_output is not None:
            SilentMode._global_output.close()

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
