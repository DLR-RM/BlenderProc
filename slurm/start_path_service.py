
import os
import sys

sys.path.append('/volume/USERSTORE/denn_ma/slurm_data/src/tensorflow_collection')

from slurm_distributor.network.slurm_path_getter import SlurmPathGetter
import glob
import argparse

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser('Starts a new service which provides the given path to various slurm workers')
    arg_parser.add_argument('service_name', help='The slurm path getter service id name')
    arg_parser.add_argument('glob_path', help='The path for the glob parser to set the right paths for the service')
    args = arg_parser.parse_args()

    if args.service_name is not None and args.glob_path is not None:
        paths = glob.glob(args.glob_path)
        if len(paths) > 0:
            slurm_path_getter = SlurmPathGetter(args.service_name, path=paths)
            if not slurm_path_getter.is_service_running():
                slurm_path_getter.setup()
            else:
                print("Is already running!")

        else:
            print("There was no found match for: {}".format(args.glob_path))

