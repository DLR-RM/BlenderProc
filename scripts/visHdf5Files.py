
import os
import h5py
import argparse
import numpy as np
from matplotlib import pyplot as plt
import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
from utils import flow_to_rgb

parser = argparse.ArgumentParser("Script to visualize hdf5 files")

parser.add_argument('hdf5', nargs='*', help='Path to hdf5 file/s')
parser.add_argument('--key', help='Key to select one of the values', default=None)

args = parser.parse_args()

if args.hdf5 is None:
	print(parser.format_help())
	exit(0)

def process_img(img, key):
	if 'distance' in key or 'seg' in key:
		img = img.astype(np.float)
		img -= np.min(img)
		max_val = np.max(img)
		if max_val != np.inf:
			img /= max_val 
		else:
			img /= np.max(img[img != np.inf])
		if len(img.shape) == 3:
			img = img[:,:,0]
	return img

def visFile(filePath, show=True):
	if os.path.exists(filePath):
		if os.path.isfile(filePath):
			with h5py.File(filePath, 'r') as data:
				if args.key is not None and args.key in [key for key in data.keys()]:
					keys = [key for key in data.keys() if key == args.key]
				else:
					keys = [key for key in data.keys()]
				for key in keys:
					val = np.array(data[key])
					if 'flow' in key and 'version' not in key:
						val = flow_to_rgb(val)

					if len(val.shape) == 2 or len(val.shape) == 3 and val.shape[2] == 3:
						plt.figure()
						plt.title("{} in {}".format(key, os.path.basename(filePath)))
						val = process_img(val, key)
						if len(val.shape) == 2 or len(val.shape) == 3 and val.shape[2] == 1:
							plt.imshow(val, cmap='jet')
						else:
							plt.imshow(val)
				if show:
					plt.show()
		else:
			print("The path is not a file")
	else:
		print("The file does not exist: {}".format(args.hdf5))

if isinstance(args.hdf5, str):
	visFile(args.hdf5)	
elif isinstance(args.hdf5, list):
	for file in args.hdf5:
		visFile(file, show=False)
	plt.show()
else:
	print("Input must be a path")
