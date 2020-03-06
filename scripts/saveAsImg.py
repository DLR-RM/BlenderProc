
import os
import h5py
import argparse
import numpy as np
import scipy.misc
import matplotlib.pyplot as plt
import cv2

parser = argparse.ArgumentParser("Script to save images out of a hdf5 files")

parser.add_argument('hdf5', nargs='*', help='Path to hdf5 file/s')

args = parser.parse_args()

if args.hdf5 is None:
	print(parser.format_help())
	exit(0)

def process_img(img, key):
	if 'depth' in key or 'seg' in key:
		img = img.astype(np.float)
		img -= np.min(img)
		max_val = np.max(img)
		if max_val != np.inf:
			img /= max_val 
		else:
			img /= np.max(img[img != np.inf])
		if len(img.shape) == 3:
			img = img[:,:,0]
	elif 'flow' in key:
		img = flow_to_rgb(img)
	return img

def flow_to_rgb(flow):
	"""
	Visualizes optical flow in hsv space and converts it to rgb space.
	:param flow: (np.array (h, w, c)) optical flow
	:return: (np.array (h, w, c)) rgb data
	"""

	im1 = flow[:, :, 0]
	im2 = flow[:, :, 1]

	h, w = flow.shape[:2]

	# Use Hue, Saturation, Value colour model
	hsv = np.zeros((h, w, 3), dtype=np.uint8)
	hsv[..., 1] = 255

	mag, ang = cv2.cartToPolar(im1, im2)
	hsv[..., 0] = ang * 180 / np.pi / 2
	hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
	return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

def visFile(filePath):
	if os.path.exists(filePath):
		if os.path.isfile(filePath):
			with h5py.File(filePath, 'r') as data:
				keys = [key for key in data.keys()]
				for key in keys:
					val = np.array(data[key])
					file_path = '{}_{}.jpg'.format(key, str(os.path.basename(filePath)).split('.')[0]) 
					if len(val.shape) == 2 or len(val.shape) == 3 and val.shape[2] == 3:
						val = process_img(val, key)
						if len(val.shape) == 2 or len(val.shape) == 3 and val.shape[2] == 1:
							plt.imsave(file_path, val, cmap='jet')
						else:
							plt.imsave(file_path, val)
		else:
			print("The path is not a file")
	else:
		print("The file does not exist: {}".format(args.hdf5))

if isinstance(args.hdf5, str):
	visFile(args.hdf5)	
elif isinstance(args.hdf5, list):
	for file in args.hdf5:
		visFile(file)
else:
	print("Input must be a path")
