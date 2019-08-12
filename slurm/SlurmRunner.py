
import os
import sys

sys.path.append('/volume/USERSTORE/denn_ma/slurm_data/src/tensorflow_collection')

from slurm_distributor.network.slurm_path_getter import SlurmPathGetter
import subprocess

class SlurmRunner(object):

    def __init__(self, service_name, config_path, args_from_path):
        self._slurm_path_getter = SlurmPathGetter(service_name, None)
        if not self._slurm_path_getter.is_service_running():
            print("The service is not running: \"{}\", start the service and rerun this program".format(service_name))
            exit(1)
        self._slurm_path_getter.setup()
        if self._slurm_path_getter.get_current_length() < 0:
            print("The service: \"{}\" has no elements left.")
            exit(1)

        self._main_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._args_from_path = args_from_path
        self._config_path = config_path

    def call(self, path):
        current_blender_pipeline = os.path.join(self._main_folder, 'run.py')

        config_path = self._config_path
        if config_path.startswith('config'):  # is a relative path
            config_path = os.path.join(self._main_folder, config_path)

        if os.path.exists(current_blender_pipeline):
            os.chdir(os.path.dirname(current_blender_pipeline))
            args = self._args_from_path(path)
            cmd = 'python {} {} {}'.format(current_blender_pipeline, config_path, " ".join(args))
            subprocess.call(cmd, shell=True)
        else:
            print("The blender pipeline run script was not found: {}".format(current_blender_pipeline))
            raise Exception('Not found!')

    def run(self):
        length = self._slurm_path_getter.get_current_length()
        while length > 0:
            new_path = self._slurm_path_getter.get_next_element()
            self.call(new_path)
            length = self._slurm_path_getter.get_current_length()







