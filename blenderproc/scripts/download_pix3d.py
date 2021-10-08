from sys import version_info, path

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import os
from urllib.request import urlretrieve, build_opener, install_opener
import shutil

from blenderproc.python.utility.SetupUtility import SetupUtility
import argparse

def cli():
    parser = argparse.ArgumentParser("Downloads the Pix3D dataset")
    parser.add_argument('output_dir', help="Determines where the data is going to be saved.")
    args = parser.parse_args()

    # setting the default header, else the server does not allow the download
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    install_opener(opener)

    pix3d_dir = args.output_dir
    if not os.path.exists(pix3d_dir):
        os.makedirs(pix3d_dir)

    # download the zip file, which contains all the obj files. Size ~3.5 GB
    print("Download the zip file, may take a while:")
    pix3d_url = "http://pix3d.csail.mit.edu/data/pix3d.zip"
    zip_file_path = os.path.join(pix3d_dir, "pix3d.zip")
    urlretrieve(pix3d_url, zip_file_path)

    # unzip the zip file
    print("Unzip the zip file.")
    SetupUtility.extract_file(pix3d_dir, zip_file_path) 

    os.remove(zip_file_path)
    shutil.rmtree(os.path.join(pix3d_dir, "img"))
    shutil.rmtree(os.path.join(pix3d_dir, "mask"))

if __name__ == "__main__":
    cli()