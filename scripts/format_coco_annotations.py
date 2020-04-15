import argparse
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--path', dest="path", type=str)

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
