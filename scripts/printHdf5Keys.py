
import h5py
import argparse
import os
import numpy as np

parser = argparse.ArgumentParser("Script to print the keys present in an hdf5 files")

parser.add_argument('hdf5', nargs='*', help='Path to hdf5 file/s')

args = parser.parse_args()

if args.hdf5 is None:
	print(parser.format_help())
	exit(0)

def processFile(file_path):
	if os.path.exists(file_path):
		with h5py.File(file_path) as data:
			keys = [key for key in data.keys()]
			if len(keys) > 0:
				key_result_list = [(key, np.array(data[key]).shape if 'version' not in key else np.array(data[key])) for key in keys]
				print("Keys: " + ', '.join(["'{}': {}".format(key, key_res) for key, key_res in key_result_list]))
if isinstance(args.hdf5, basestring):
	procressFile(args.hdf5)	
elif isinstance(args.hdf5, list):
	for file in args.hdf5:
		processFile(file)
else:
	print("Input must be a path")

