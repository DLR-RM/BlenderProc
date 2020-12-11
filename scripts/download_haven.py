
from sys import version_info
if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import zipfile
from io import BytesIO

from requests import get
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--resolution', help="Desired resolution for the hdr images. Be aware that bigger resolutions, "
                                         "take a lot of disc space.", default="2k")
parser.add_argument('--format', help="Desired download format for the images.", default="jpg")
output_dir = Path(__file__).parent / ".." / "resources" / "haven"
parser.add_argument('--output_folder', help="Determines where the data is going to be saved.", default=output_dir)
args = parser.parse_args()

output_dir = Path(args.output_folder)


def download_items(list_url, output_dir, item_download_func):
    print("Downloading " + output_dir.name + "...")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download listing
    response = get(list_url)
    html_soup = BeautifulSoup(response.text, 'html.parser')

    # Extract items
    items = html_soup.find('div', id='item-grid')
    children = list(items.children)

    for i, item in enumerate(children):
        if "href" in item.attrs:
            # Get item_id and download the item
            item_id = item.attrs["href"].split("=")[-1]
            item_output = output_dir / item_id
            item_output.mkdir(exist_ok=True)
            print("({}/{}) {}".format(i, len(children), item_id))
            item_download_func(item_id, item_output)

def download_texture(item_id, output_dir):
    download_url = "https://texturehaven.com/files/textures/zip/2k/{}/{}_{}_{}.zip".format(item_id, item_id,
                                                                                           args.resolution, args.format)
    request = requests.get(download_url)
    with zipfile.ZipFile(BytesIO(request.content)) as tar:
        tar.extractall(str(output_dir))

def download_hdri(item_id, output_dir):
    download_url = "https://hdrihaven.com/files/hdris/{}_{}.hdr".format(item_id, args.resolution)
    request = requests.get(download_url)
    with open(output_dir / download_url.split("/")[-1], "wb") as file:
        file.write(request.content)

def download_model(item_id, output_dir):
    # Download item's html page
    response = get("https://3dmodelhaven.com/model/?m={}".format(item_id))
    html_soup = BeautifulSoup(response.text, 'html.parser')
    # Go over all download files
    items = html_soup.find('div', class_='fake-table')
    for file in items.find_all("a"):
        # Download single file
        download_url = file.attrs["href"]
        request = requests.get("https://3dmodelhaven.com/" + download_url)
        # Determine output path
        destination = output_dir / download_url[len("/files/models/{}/".format(item_id)):]
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "wb") as file:
            file.write(request.content)

download_items("https://texturehaven.com/textures/", output_dir / "textures", download_texture)
download_items("https://hdrihaven.com/hdris/", output_dir / "hdris", download_hdri)
download_items("https://3dmodelhaven.com/models/", output_dir / "models", download_model)