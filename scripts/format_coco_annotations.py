""" Formats the coco annotations .json file.

When generating coco annotations for the rendered pipeline's images, some annotations may be corrupted due to objects
being barely visible in the image: only 1px of the object being visible in the camera's fov leads to the empty
segmentation mask and an annotation of wrong width/height. Those faulty annotations bring nothing useful to the table
during training.

When supplied with a path to a .json file, this script iterates through all annotations of this file, deletes ones with
an empty segmentation masks, and then saves the formatted result a a new .json file.

Input parameters:
    * -p, --path: path to a .json coco annotations file.
"""

import argparse
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--path', dest="path", type=str, help='path to a coco annotations .json file')

args = parser.parse_args()

path = args.path

with open(args.path) as file:
    data = json.load(file)

for i in range(len(data['annotations']) - 1, -1, -1):
    if len(data['annotations'][i]['segmentation']) == 0:
        del data['annotations'][i]

new_path = os.path.join(os.path.dirname(path), os.path.basename(path).split('.')[0] + '_formatted.json')
with open(new_path, 'w') as f:
    json.dump(data, f)
