
import os
import sys

sys.path.append('/volume/USERSTORE/denn_ma/slurm_data/src/tensorflow_collection/slurm_distributor')

from slurm_distributor.network.slurm_path_getter import SlurmPathGetter
import glob
import argparse

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('Runs the blender pipeline in combination with the slurm path getter')
    arg_parser.add_argument('--service_name_for_cam_poses', help='The slurm path getter service id name for getting camera poses', required=True)
    arg_parser.add_argument('--glob_camera_path', help='The path for the glob parser to set the right paths for the service', required=True)
    args = arg_parser.parse_args()

    if args.service_name_for_cam_poses is not None and args.glob_camera_path is not None:
        service_name = args.service_name_for_cam_poses
        paths = glob.glob(args.glob_camera_path)
        if len(paths) > 0:
            slurm_path_getter = SlurmPathGetter(service_name, path=paths)
            if not slurm_path_getter.is_service_running():
                slurm_path_getter.setup()
            else:
                print("Is already running!")

        else:
            print("There was no found match for: {}".format(args.glob_camera_path))

