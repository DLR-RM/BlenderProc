import argparse
import json
import os
import numpy as np
from PIL import Image, ImageFont, ImageDraw

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest='conf', default='coco_annotations.json', help='coco annotation json file')
    parser.add_argument('-i', '--image_index', dest='image_index', default=0, help='image over which to annotate, uses the rgb rendering', type=int)
    parser.add_argument('-b', '--base_path', dest='base_path', default='examples/advanced/coco_annotations/output/coco_data', help='path to folder with coco_annotation.json and images', type=str)
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
        images = annotations['images']
        annotations = annotations['annotations']

    im = Image.open(os.path.join(base_path, images[image_idx]['file_name']))

    def get_category(_id):
        category = [category["name"] for category in categories if category["id"] == _id]
        if len(category) != 0:
            return category[0]
        else:
            raise Exception("Category {} is not defined in {}".format(_id, os.path.join(base_path, conf)))

    def rle_to_binary_mask(rle):
        """Converts a COCOs run-length encoding (RLE) to binary mask.
        :param rle: Mask in RLE format
        :return: a 2D binary numpy array where '1's represent the object
        """
        binary_array = np.zeros(np.prod(rle.get('size')), dtype=np.bool)
        counts = rle.get('counts')

        start = 0
        for i in range(len(counts)-1):
            start += counts[i]
            end = start + counts[i+1]
            binary_array[start:end] = (i + 1) % 2

        binary_mask = binary_array.reshape(*rle.get('size'), order='F')

        return binary_mask

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
                rle_seg = annotation["segmentation"]
                item = rle_to_binary_mask(rle_seg).astype(np.uint8) * 255
                item = Image.fromarray(item, mode='L')
                overlay = Image.new('RGBA', im.size)
                draw_ov = ImageDraw.Draw(overlay)
                rand_color = np.random.randint(0,256,3)
                draw_ov.bitmap((0, 0), item, fill=(rand_color[0], rand_color[1], rand_color[2], 128))
                im = Image.alpha_composite(im, overlay)
            else:
                # go through all polygons and plot them
                for item in annotation['segmentation']:
                    poly = Image.new('RGBA', im.size)
                    pdraw = ImageDraw.Draw(poly)
                    rand_color = np.random.randint(0,256,3)
                    pdraw.polygon(item, fill=(rand_color[0], rand_color[1], rand_color[2], 127), outline=(255, 255, 255, 255))
                    im.paste(poly, mask=poly)
    if save:
        im.save(os.path.join(base_path, 'coco_annotated_{}.png'.format(image_idx)), "PNG")
    im.show()

if __name__ == "__main__":
    cli()