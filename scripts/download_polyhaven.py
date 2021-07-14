from sys import version_info

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import requests
from pathlib import Path
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--resolution', help="Desired resolution for the hdr images and textures. Be aware that bigger "
                                         "resolutions take a lot of disc space.", default="2k")
parser.add_argument('--format', help="Desired download format for the images.", default="jpg")
output_dir = Path(__file__).parent / ".." / "resources" / "polyhaven"
parser.add_argument('--output_folder', help="Determines where the data is going to be saved.", default=output_dir)
parser.add_argument('--tags', nargs='+', help="Filter by asset Tag.", default=None)
parser.add_argument('--categories', nargs='+', help="Filter by asset Category.", default=None)
parser.add_argument('--type', help="Filter by asset Type.", default=None)
args = parser.parse_args()

output_dir = Path(args.output_folder)


def get_assets(asset_type=None, categories=None, tags=None):
    if categories:
        categories = ",".join(categories)
    params = {"type": asset_type, "categories": categories}
    assets = requests.get("https://api.polyhaven.com/assets", params=params).json()

    if not tags:
        return assets

    new_dict = dict()
    for (key, value) in assets.items():
        if any(tag_list in tags for tag_list in value.get("tags")):
            new_dict[key] = value

    return new_dict


def download_file(url, destination):
    request = requests.get(url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "wb") as file:
        file.write(request.content)


def download_model(asset_id, asset, output_dir, resolution):
    print("downloading model", asset["name"])
    files = requests.get("https://api.polyhaven.com/files/" + str(asset_id)).json()

    # only download .blend file for models
    o = files["blend"][resolution]["blend"]
    main_url = o["url"]
    destination = output_dir / asset_id
    download_file(main_url, destination / os.path.basename(main_url))
    incls = o["include"]
    for (filename, incl) in incls.items():
        i_url = incl["url"]
        download_file(i_url, destination / filename)


def download_texture(asset_id, asset, output_dir, img_format, resolution):
    print("downloading texture", asset["name"])
    files = requests.get("https://api.polyhaven.com/files/" + str(asset_id)).json()
    destination = output_dir / asset_id

    for (key, value) in files.items():
        res = value.get(resolution)
        if res:
            fmt = res.get(img_format)
            if fmt:
                url = fmt.get("url")
                if url:
                    download_file(url, destination / os.path.basename(url))


def download_hdri(asset_id, asset, output_dir, img_format, resolution):
    print("downloading hdri", asset["name"])
    files = requests.get("https://api.polyhaven.com/files/" + str(asset_id)).json()
    destination = output_dir / asset_id

    res = files.get("hdri").get(resolution)
    if res:
        url = res.get("hdr").get("url")
        download_file(url, destination / os.path.basename(url))


def download_items(output_dir, resolution, img_format, asset_type, categories, tags):
    assets = get_assets(asset_type, categories, tags)
    num_assets = len(assets.keys())
    print("found ", num_assets, "assets")

    asset_count = 0
    for (asset_id, asset) in assets.items():
        asset_count += 1
        print("Asset", asset_count, "/", num_assets)
        if asset["type"] == 2:
            download_model(asset_id, asset, output_dir / "models", resolution)
        elif asset["type"] == 1:
            download_texture(asset_id, asset, output_dir / "textures", img_format, resolution)
        elif asset["type"] == 0:
            download_hdri(asset_id, asset, output_dir / "hdris", img_format, resolution)


download_items(output_dir, args.resolution, args.format, args.type, args.categories, args.tags)
