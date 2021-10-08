from sys import version_info
if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import os
from urllib.request import urlretrieve, build_opener, install_opener
from blenderproc.python.utility.SetupUtility import SetupUtility
import argparse

def cli():
    parser = argparse.ArgumentParser("Downloads the scenenet dataset")
    parser.add_argument('output_dir', help="Determines where the data is going to be saved.")
    args = parser.parse_args()

    # setting the default header, else the server does not allow the download
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    install_opener(opener)

    scenenet_dir = args.output_dir
    if not os.path.exists(scenenet_dir):
        os.makedirs(scenenet_dir)

    # download the zip file, which contains all the obj files
    print("Download the zip file, may take a while:")
    scenenet_url = "https://bitbucket.org/robotvault/downloadscenenet/get/cfe5ab85ddcc.zip"
    zip_file_path = os.path.join(scenenet_dir, "scene_net.zip")
    urlretrieve(scenenet_url, zip_file_path)

    # unzip the zip file
    print("Unzip the zip file.")
    SetupUtility.extract_file(scenenet_dir, zip_file_path) 

    os.remove(zip_file_path)
    os.rename(os.path.join(scenenet_dir, "robotvault-downloadscenenet-cfe5ab85ddcc"), os.path.join(scenenet_dir, "SceneNetData"))

    print("Please also download the texture library from here: http://tinyurl.com/zpc9ppb")
    print("This is a google drive folder downloading via script is tedious.")

if __name__ == "__main__":
    cli()