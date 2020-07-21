import argparse
import json
import os

import numpy as np
from PIL import Image, ImageFont, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--conf', dest='conf', default='coco_annotations.json', help='coco annotation json file')
parser.add_argument('-i', '--image_index', dest='image_index', default=0, help='image over which to annotate, uses the rgb rendering', type=int)
parser.add_argument('-b', '--base_path', dest='base_path', default='examples/coco_annotations/output/coco_data', help='path to folder with coco_annotation.json and images', type=str)
parser.add_argument('--save', '-s', action='store_true', help='saves visualization of coco annotations under base_path/coco_annotated_x.png ')

args = parser.parse_args()

conf = args.conf
image_idx = args.image_index
base_path = args.base_path
save = args.save

# Read coco_annotations config
with open(os.path.join(base_path, conf)) as f:
    annotations = json.load(f)
    categories = annotations['categories']
    annotations = annotations['annotations']

im_path = os.path.join(base_path, "rgb_{:04d}.png".format(image_idx))
if os.path.exists(im_path):
    im = Image.open(im_path)
else:
    im = Image.open(im_path.replace('png', 'jpg'))

draw = ImageDraw.Draw(im)


def get_category(_id):
    category = [category["name"] for category in categories if category["id"] == _id]
    if len(category) != 0:
        return category[0]
    else:
        raise Exception("Category {} is not defined in {}".format(_id, os.path.join(base_path, conf)))


def rle2mask(rle, width, height):
    mask = np.zeros(width * height)
    array = np.asarray([int(x) for x in rle])
    starts = array[0::2]
    lengths = array[1::2]
    current_position = 0
    for index, start in enumerate(starts):
        current_position += start
        print(index)
        mask[current_position:current_position+lengths[index]] = 1
        current_position += lengths[index]
    return mask.reshape(width, height)


font = ImageFont.load_default()
# Add bounding boxes and masks
for idx, annotation in enumerate(annotations):
    if annotation["image_id"] == image_idx:
        bb = annotation['bbox']
        draw.rectangle(((bb[0], bb[1]), (bb[0] + bb[2], bb[1] + bb[3])), fill=None, outline="red")
        draw.text((bb[0] + 2, bb[1] + 2), get_category(annotation["category_id"]), font=font)
        if annotation["iscrowd"]:
            item = rle2mask(annotation["segmentation"]["counts"], annotation["segmentation"]["size"][0], annotation["segmentation"]["size"][1])
        else:
            item = annotation["segmentation"][0]
        poly = Image.new('RGBA', im.size)
        pdraw = ImageDraw.Draw(poly)
        pdraw.polygon(item, fill=(255, 255, 255, 127), outline=(255, 255, 255, 255))
        im.paste(poly, mask=poly)
if save:
    im.save(os.path.join(base_path, 'coco_annotated_{}.png'.format(image_idx)), "PNG")
im.show()
