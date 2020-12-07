from sys import version_info

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import os
from urllib.request import urlretrieve, build_opener, install_opener
import glob
import subprocess
import shutil

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
    cmd = "unzip {} > /dev/null".format(zip_file_path)
    subprocess.call(cmd, shell=True, cwd=os.path.dirname(zip_file_path))

    os.remove(zip_file_path)
    ikea_dir = os.path.join(ikea_dir, "IKEA")

    subprocess.call("chmod -R a+rw *", shell=True, cwd=ikea_dir)

    print("The IKEA dataset has some weird bugs, these are fixed now.")
    if os.path.exists(os.path.join(ikea_dir, "IKEA_bed_BEDDINGE")):
        shutil.rmtree(os.path.join(ikea_dir, "IKEA_bed_BEDDINGE"))

    nils_folder = os.path.join(ikea_dir, "IKEA_chair_NILS")
    if os.path.exists(nils_folder):
        print(glob.glob(os.path.join(nils_folder, "*")))

    # delete all no double .obj
    for folder in glob.glob(os.path.join(ikea_dir, "*")):
        no_jitter_folders = glob.glob(os.path.join(folder, "nojitter*"))
        org_obj_files = glob.glob(os.path.join(folder, ".obj"))
        for org_obj_file in org_obj_files:
            os.remove(org_obj_file)
        if no_jitter_folders:
            for no_jitter_folder in no_jitter_folders:
                obj_files = glob.glob(os.path.join(no_jitter_folder, "*.obj"))
                # first remove all the ones without mtl
                for obj_file in obj_files:
                    new_name = obj_file.replace(os.path.basename(os.path.dirname(obj_file)), "")
                    os.rename(obj_file, new_name)
                    os.rename(obj_file.replace(".obj", ".mtl"), new_name.replace(".obj", ".mtl"))
                jpg_files = glob.glob(os.path.join(no_jitter_folder, "*.jpg"))
                for jpg_file in jpg_files:
                    new_name = jpg_file.replace(os.path.basename(os.path.dirname(jpg_file)), "")
                    os.rename(jpg_file, new_name)
                folders_in_no_jitter = [f for f in glob.glob(os.path.join(no_jitter_folder, "*")) if os.path.isdir(f)]
                for mv_folder in folders_in_no_jitter:
                    new_name = mv_folder.replace(os.path.basename(os.path.dirname(mv_folder)), "")
                    os.rename(mv_folder, new_name)

    # delete no jitter
    for folder in glob.glob(os.path.join(ikea_dir, "*", "nojitter*")):
        shutil.rmtree(folder)

    # delete all skp files
    skp_files = glob.glob(os.path.join(ikea_dir, "*", "*.skp"))
    for skp_file in skp_files:
        os.remove(skp_file)

    # delete all json files
    js_files = glob.glob(os.path.join(ikea_dir, "*", "*.js"))
    for js_file in js_files:
        os.remove(js_file)

    # delete specific files which need to broken up:
    def delete_obj_file(path):
        os.remove(path)
        if os.path.exists(path.replace(".obj", ".mtl")):
            os.remove(path.replace(".obj", ".mtl"))

    # this are several couches in one object file
    first_path = os.path.join(ikea_dir, "IKEA_sofa_VRETA", "3b58f55ed32ceef86315023d0bef39b6_obj0_object.obj")














