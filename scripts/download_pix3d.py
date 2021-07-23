from sys import version_info, path

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import os
from urllib.request import urlretrieve, build_opener, install_opener
import shutil

from utils import ProgressBar
path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.utility.SetupUtility import SetupUtility


if __name__ == "__main__":
    # setting the default header, else the server does not allow the download
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    install_opener(opener)

    # set the download directory relative to this one
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pix3d_dir = os.path.join(current_dir, "..", "resources", "pix3d")

    if not os.path.exists(pix3d_dir):
        os.makedirs(pix3d_dir)

    # download the zip file, which contains all the obj files. Size ~3.5 GB
    print("Download the zip file, may take a while:")
    pix3d_url = "http://pix3d.csail.mit.edu/data/pix3d.zip"
    zip_file_path = os.path.join(pix3d_dir, "pix3d.zip")
    urlretrieve(pix3d_url, zip_file_path, ProgressBar())

    # unzip the zip file
    print("Unzip the zip file.")
    SetupUtility.extract_file(pix3d_dir, zip_file_path) 

    os.remove(zip_file_path)
    shutil.rmtree(os.path.join(pix3d_dir, "img"))
    shutil.rmtree(os.path.join(pix3d_dir, "mask"))