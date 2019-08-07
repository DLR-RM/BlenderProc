
import os
import sys

sys.path.append('/volume/USERSTORE/denn_ma/slurm_data/src/tensorflow_collection/slurm_distributor')

from slurm_distributor.network.slurm_path_getter import SlurmPathGetter
import argparse
import subprocess

class SlurmRunner(object):

    def __init__(self, service_name_for_cam_poses, config_path='config/suncg_basic.json', house_path='/volume/reconstruction_data/suncg/improved_data/version_1.0.0/house'):
        self._slurm_path_getter = SlurmPathGetter(service_name, None)
        if not self._slurm_path_getter.is_service_running():
            print("The service is not running: \"{}\", start the service and rerun this program".format(service_name_for_cam_poses))
            exit(1)
        self._slurm_path_getter.setup()
        if self._slurm_path_getter.get_current_length() < 0:
            print("The service: \"{}\" has no elements left.")
            exit(1)
        self._main_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._house_path = house_path
        self._config_path = config_path

    def get_house_json_from_cam_path(self, cam_path):
        house_id = os.path.basename(os.path.dirname(cam_path))
        return os.path.join(self._house_path, house_id, 'house.json')

    def call(self, camera_path, house_json_path):
        current_blender_pipeline = os.path.join(self._main_folder, 'run.py')
        config_path = self._config_path
        if config_path.startswith('config'):  # is a relative path
            config_path = os.path.join(self._main_folder, config_path)
        if os.path.exists(current_blender_pipeline):
            os.chdir(os.path.dirname(current_blender_pipeline))
            cmd = 'python {} {} {} {}'.format(current_blender_pipeline, config_path, camera_path, house_json_path)
            subprocess.call(cmd, shell=True)
        else:
            print("The blender pipeline run script was not found: {}".format(current_blender_pipeline))
            raise Exception('Not found!')

    def run(self):
        length = self._slurm_path_getter.get_current_length()
        while length > 0:
            new_camera_path = self._slurm_path_getter.get_next_element()
            new_house_json_path = self.get_house_json_from_cam_path(new_camera_path)
            if os.path.exists(new_camera_path) and os.path.exists(new_house_json_path):
                self.call(new_camera_path, new_house_json_path)
            length = self._slurm_path_getter.get_current_length()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('Runs the blender pipeline in combination with the slurm path getter')
    arg_parser.add_argument('--service_name_for_cam_poses', help='The slurm path getter service id name for getting camera poses', required=True)
    args = arg_parser.parse_args()

    if args.service_name_for_cam_poses is not None:
        service_name = args.service_name_for_cam_poses
        slurm_runner = SlurmRunner(service_name)
        slurm_runner.run()






