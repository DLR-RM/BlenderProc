
import os
import sys

sys.path.append('/volume/USERSTORE/denn_ma/slurm_data/src/tensorflow_collection')

from slurm_distributor.network.slurm_path_getter import SlurmPathGetter
import subprocess

class SlurmRunner(object):

    def __init__(self, service_name, config_path, args_from_path):
        self._slurm_path_getter = SlurmPathGetter(service_name, None)
        # Make sure the service is running
        if not self._slurm_path_getter.is_service_running():
            print("The service is not running: \"{}\", start the service and rerun this program".format(service_name))
            exit(1)
        self._slurm_path_getter.setup()

        # Make sure the service has still elements in its queue
        if self._slurm_path_getter.get_current_length() < 0:
            print("The service: \"{}\" has no elements left.")
            exit(1)

        # Determine blender pipeline main directory (Parent dir of parent dir of this file)
        self._main_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._args_from_path = args_from_path
        self._config_path = config_path

    def call(self, path):
        current_blender_pipeline = os.path.join(self._main_folder, 'run.py')

        # Determine absolute path to config file
        config_path = self._config_path
        if config_path.startswith('config'):  # is a relative path
            config_path = os.path.join(self._main_folder, config_path)

        if os.path.exists(current_blender_pipeline):
            os.chdir(os.path.dirname(current_blender_pipeline))

            # Determine command line arguments for the current path
            args = self._args_from_path(path)

            # Start blender pipeline with given arguments
            cmd = 'python {} {} {}'.format(current_blender_pipeline, config_path, " ".join(args))
            subprocess.call(cmd, shell=True)
        else:
            print("The blender pipeline run script was not found: {}".format(current_blender_pipeline))
            raise Exception('Not found!')

    def run(self):
        # Do as long as there are still elements in the queue
        while self._slurm_path_getter.get_current_length() > 0:
            # Process next element
            new_path = self._slurm_path_getter.get_next_element()
            self.call(new_path)







