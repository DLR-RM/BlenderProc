from sys import version_info

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import os
from urllib.request import urlretrieve, build_opener, install_opener
import subprocess


if __name__ == "__main__":
    # setting the default header, else the server does not allow the download
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    install_opener(opener)

    # set the download directory relative to this one
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ikea_dir = os.path.join(current_dir, "..", "resources", "IKEA")

    if not os.path.exists(ikea_dir):
        os.makedirs(ikea_dir)

    # download the zip file, which contains all the model files.
    print("Downloading the zip file (166mb)...")
    ikea_url = "http://ikea.csail.mit.edu/zip/IKEA_models.zip"
    zip_file_path = os.path.join(ikea_dir, "IKEA_models.zip")
    urlretrieve(ikea_url, zip_file_path)
    print("Download complete.")

    # unzip the zip file
    print("Unzipping the zip file...")
    cmd = "unzip {}".format(zip_file_path)
    subprocess.call(cmd, shell=True, cwd=os.path.dirname(zip_file_path))

    os.remove(zip_file_path)
