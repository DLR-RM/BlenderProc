import os

from blenderproc.python.utility.Utility import Utility, resolve_path


class Module:
    """
    **Configuration**:

    All of these values can be set per Module or of the global config defined in the main.Initializer:

    .. code-block:: yaml

      {
        "module": "main.Initializer",
        "config":{
          "global": {
            "output_dir": "<args:X>"
          }
        }
      }

    If they are set globally all modules will inherit them, if there is no module defined key available.

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - output_is_temp
          - If True, all files created in this module will be written into the temp_dir. If False, the output_dir is
            used. 
          - bool
        * - output_dir
          - The path to a directory where all persistent output files should be stored. If it doesn't exist, it is
            created automatically. Default: "".
          - string
        * - avoid_output
          - This mode is only used during debugging, when no output should be produced. Default: False
          - bool
    """

    def __init__(self, config):
        self.config = config
        self._default_init()

    def _default_init(self):
        """
        These operations are called during all modules inits
        """
        self._output_dir = resolve_path(self.config.get_string("output_dir", ""))
        os.makedirs(self._output_dir, exist_ok=True)

        self._temp_dir = Utility.get_temporary_directory()

        self._avoid_output = self.config.get_bool("avoid_output", False)

    def _determine_output_dir(self, output_is_temp_default=True):
        """ Returns the directory where to store output file created by this module.

        :param output_is_temp_default: True, if the files created by this module should be temporary by default.
        :return: The output directory to use
        """
        if self.config.get_bool("output_is_temp", output_is_temp_default):
            return self._temp_dir
        else:
            return self._output_dir
