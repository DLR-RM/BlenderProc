
import h5py
import argparse
import os
import numpy as np

parser = argparse.ArgumentParser("Script to print the keys present in an hdf5 files")

parser.add_argument('hdf5', nargs='*', help='Path to hdf5 file/s')
parser.add_argument('--key', help='If a key is specified only the key will be shown')

args = parser.parse_args()

if args.hdf5 is None:
    print(parser.format_help())
    exit(0)

asked_key = args.key


def processFile(file_path):
    if os.path.exists(file_path):
        with h5py.File(file_path, "r") as data:
            if asked_key:
                keys = [key for key in data.keys() if asked_key in key]
            else:
                keys = [key for key in data.keys()]
            if len(keys) > 0:
                res = []
                for key in keys:
                    current_res = np.array(data[key])
                    if sum([ele for ele in current_res.shape]) < 5 or "version" in key:
                        if current_res.dtype == "|S5":
                            res.append((key, str(current_res).replace("[", "").replace("]", "").replace("b'", "").replace("'", "")))
                        else:
                            res.append((key, current_res))
                    else:
                        res.append((key, current_res.shape))
                res = ["'{}': {}".format(key, key_res) for key, key_res in res]
                print("Keys: " + ', '.join(res))

if isinstance(args.hdf5, str):
    processFile(args.hdf5)
elif isinstance(args.hdf5, list):
    for file in args.hdf5:
        processFile(file)
else:
    print("Input must be a path")


    

