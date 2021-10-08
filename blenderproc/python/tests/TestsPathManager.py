import os
from os.path import dirname, abspath, join, exists
from blenderproc.python.utility.Utility import resolve_path, Utility


class TestsPathManager(object):
    """
    The TestsPathManager keeps track of all used paths in the tests and allows setting them via environment variables.
    To allow testing in environments, where the paths are not the default ones.
    """

    def __init__(self):
        """
        """
        self._main_folder = Utility.blenderproc_root

        # for the default resource folder, this one should always be available
        self.example_resources = abspath(join(self._main_folder, "examples/resources"))

        # for cc materials
        self._add_parameter("cc_materials", "resources/cctextures", "BP_CC_MATERIALS_PATH")

        self._add_parameter("haven", "resources/haven", "BP_HAVEN_PATH")

    def _add_parameter(self, param_name: str, default_path: str, environment_key: str):
        """
        Adds an parameter to the object, the name of the parameter is defined by the param_name. The default_path is
        only used if it exists, if it does not exists the environment_key is used. An error is thrown if both do
        not exist.

        :param param_name: Name of the new parameter
        :param default_path: Default path used for this parameter
        :param environment_key: Environment key which has to be set if the default path does not exist
        """
        setattr(self, param_name, abspath(join(self._main_folder, default_path)))
        if not exists(getattr(self, param_name)):
            if environment_key in os.environ:
                setattr(self, param_name, resolve_path(os.environ[environment_key]))
            if not exists(getattr(self, param_name)):
                raise Exception(f"The env variable: \"{environment_key}\" is empty or does not exist and the default "
                                f"path does also not exist: {default_path}")


test_path_manager = TestsPathManager()


