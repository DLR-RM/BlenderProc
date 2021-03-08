import os
import random
import argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--images", type=str, help="Path to object images to paste.")
parser.add_argument("-b", "--backgrounds", type=str, help="Path to background images to paste on.")
parser.add_argument("-t", "--types", default=('jpg', 'jpeg', 'png'), type=str, nargs='+',
                    help="File types to consider. Default: JP[E]G, PNG.")
parser.add_argument("-o", "--overwrite", action="store_true", help="Stores merged images to object image file paths.")
args = parser.parse_args()

if not args.overwrite:
    os.makedirs(os.path.join(args.images, "out"), exist_ok=True)

for file_name in os.listdir(args.images):
    if file_name.lower().endswith(args.types):
        img_path = os.path.join(args.images, file_name)
        img = Image.open(img_path)
        img_w, img_h = img.size

        background_path = random.choice(
            [os.path.join(args.backgrounds, p) for p in os.listdir(args.backgrounds) if p.lower().endswith(args.types)])
        background = Image.open(background_path).resize([img_w, img_h])
        background.paste(img, mask=img.convert('RGBA'))
        if args.overwrite:
            background.save(img_path)
        else:
            background.save(os.path.join(args.images, "out", file_name))
