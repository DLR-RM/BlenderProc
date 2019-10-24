
import os

from SlurmRunner import SlurmRunner

import argparse

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('Runs the blender pipeline by using the camera files provided by the given service')
    arg_parser.add_argument('service_name_for_cam_poses', help='The slurm path getter service id name for getting camera poses')
    arg_parser.add_argument('output_dir', help='The path were to store the output files.')
    arg_parser.add_argument('--config', default='examples/suncg_basic/config.yaml')
    arg_parser.add_argument('--houses', default='/volume/reconstruction_data/suncg/improved_data/version_1.0.0/house')
    args = arg_parser.parse_args()

    def args_from_path(cam_pose_path):
        house_id = os.path.basename(os.path.dirname(cam_pose_path))

        pipeline_args = []
        # Cam pose
        pipeline_args.append(cam_pose_path)
        # House.json
        pipeline_args.append(os.path.join(args.houses, house_id, 'house.json'))
        # Output dir
        pipeline_args.append(os.path.join(args.output_dir, house_id))

        return pipeline_args

    if args.service_name_for_cam_poses is not None:
        service_name = args.service_name_for_cam_poses
        slurm_runner = SlurmRunner(service_name, args.config, args_from_path)
        slurm_runner.run()






