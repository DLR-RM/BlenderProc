
import os

from SlurmRunner import SlurmRunner

import argparse

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('Runs the blender pipeline by using the house.json files provided by the given service')
    arg_parser.add_argument('service_name_for_house_jsons', help='The slurm path getter service id name for getting house jsons')
    arg_parser.add_argument('output_dir', help='The path were to store the output files')
    arg_parser.add_argument('--config', default='config/suncg_with_cam_sampling.json')
    args = arg_parser.parse_args()

    def args_from_path(house_path):
        house_id = os.path.basename(os.path.dirname(house_path))

        pipeline_args = []
        # House.json
        pipeline_args.append(house_path)
        # Output dir
        pipeline_args.append(os.path.join(args.output_dir, house_id))

        return pipeline_args

    if args.service_name_for_house_jsons is not None:
        service_name = args.service_name_for_house_jsons
        slurm_runner = SlurmRunner(service_name, args.config, args_from_path)
        slurm_runner.run()






