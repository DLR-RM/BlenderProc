import argparse
import json
import os

from pycocotools import mask
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

def get_category(_id):
    category = [category["name"] for category in categories if category["id"] == _id]
    if len(category) != 0:
        return category[0]
    else:
        raise Exception("Category {} is not defined in {}".format(_id, os.path.join(base_path, conf)))


font = ImageFont.load_default()
# Add bounding boxes and masks
for idx, annotation in enumerate(annotations):
    if annotation["image_id"] == image_idx:
        draw = ImageDraw.Draw(im)
        bb = annotation['bbox']
        draw.rectangle(((bb[0], bb[1]), (bb[0] + bb[2], bb[1] + bb[3])), fill=None, outline="red")
        draw.text((bb[0] + 2, bb[1] + 2), get_category(annotation["category_id"]), font=font)
        if isinstance(annotation["segmentation"], dict):
            im.putalpha(255)
            an_sg = annotation["segmentation"]
            item = mask.decode(mask.frPyObjects(an_sg, im.size[1], im.size[0])).astype(np.uint8) * 255
            item = Image.fromarray(item, mode='L')
            overlay = Image.new('RGBA', im.size)
            draw_ov = ImageDraw.Draw(overlay)
            draw_ov.bitmap((0, 0), item, fill=(255, 0, 0, 128))
            im = Image.alpha_composite(im, overlay)
        else:
            item = annotation["segmentation"][0]
            poly = Image.new('RGBA', im.size)
            pdraw = ImageDraw.Draw(poly)
            pdraw.polygon(item, fill=(255, 255, 255, 127), outline=(255, 255, 255, 255))
            im.paste(poly, mask=poly)
if save:
    im.save(os.path.join(base_path, 'coco_annotated_{}.png'.format(image_idx)), "PNG")
im.show()
