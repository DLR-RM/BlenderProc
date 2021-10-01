from sys import version_info, path

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import os
from urllib.request import urlretrieve, build_opener, install_opener
import glob
import numpy as np
import subprocess
import shutil
import argparse

from blenderproc.python.utility.SetupUtility import SetupUtility

def split_object_according_to_groups(file_path, folder):
    """
    Splits the given .obj file into different objects, assuming these objects have been separated via groups before.

    :param file_path: Path to the .obj file
    :param folder: Folder in which the resulting split .obj files we be saved
    """
    with open(file_path, "r") as file:
        text = file.read()
        lines = text.split("\n")
        start_info = ""
        for line in lines:
            if line.strip().startswith("g "):
                break
            else:
                start_info += line + "\n"

        list_of_split_ids = [i for i, line in enumerate(lines) if line.strip().startswith("g ")]
        last_i = list_of_split_ids[0]
        group_counter = 0
        for index, current_i in enumerate(list_of_split_ids[1:]):
            current_text = start_info
            current_lines = lines[last_i: current_i]
            face_lines = [l[len("f "):].strip().split(" ") for l in current_lines if l.strip().startswith("f ")]
            face_lines = np.array([[[int(e) for e in eles.split("/")] for eles in l] for l in face_lines])
            face_offset = np.min(face_lines, axis=0)
            face_offset = np.min(face_offset, axis=0) - 1

            final_lins = []
            for line in current_lines:
                if line.strip().startswith("f "):
                    blocks = line[len("f "):].strip().split(" ")
                    values = [np.array([int(e) for e in eles.split("/")]) - face_offset for eles in blocks]
                    f_line = "f " + " ".join(["/".join([str(int(e)) for e in eles]) for eles in values])
                    final_lins.append(f_line)
                else:
                    final_lins.append(line)
            last_i = current_i

            amount_of_faces = sum([1 for l in final_lins if l.startswith("f ")])
            if amount_of_faces > 10:
                current_text += "\n".join(final_lins)
                with open(os.path.join(folder, "{}_{}.obj".format(os.path.basename(folder), group_counter)), "w") as f:
                    f.write(current_text)
                group_counter += 1


def cli():
    parser = argparse.ArgumentParser("Downloads the IKEA dataset")
    parser.add_argument('output_dir', help="Determines where the data is going to be saved.")
    args = parser.parse_args()

    # setting the default header, else the server does not allow the download
    opener = build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    install_opener(opener)

    ikea_dir = args.output_dir
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
    ikea_dir = os.path.join(ikea_dir, "IKEA")
    SetupUtility.extract_file(ikea_dir, zip_file_path) 
    os.remove(zip_file_path)

    subprocess.call("chmod -R a+rw *", shell=True, cwd=ikea_dir)

    print("The IKEA dataset has some weird bugs, these are fixed now.")
    if os.path.exists(os.path.join(ikea_dir, "IKEA_bed_BEDDINGE")):
        shutil.rmtree(os.path.join(ikea_dir, "IKEA_bed_BEDDINGE"))

    nils_folder = os.path.join(ikea_dir, "IKEA_chair_NILS")
    if os.path.exists(nils_folder):
        shutil.rmtree(nils_folder)

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

    # directly remove these files:
    path = os.path.join(ikea_dir, "IKEA_wardrobe_PAX", "4b91d887fd34890a35d389147630ded_obj0_object.obj")
    delete_obj_file(path)
    path = os.path.join(ikea_dir, "IKEA_chair_JOKKMOKK", "221da64f5789c4bfcf7d397dd220c7e2_obj0_object.obj")
    delete_obj_file(path)
    path = os.path.join(ikea_dir, "IKEA_table_JOKKMOKK", "jokkmokk_table_2_obj0_object.obj")
    delete_obj_file(path)
    path = os.path.join(ikea_dir, "IKEA_table_UTBY", "cfcd08bbf590325e7b190cd56debb387_obj0_object.obj")
    delete_obj_file(path)
    path = os.path.join(ikea_dir, "IKEA_chair_STEFAN", "7e44c6d0933417ace05f257fa4ec4037_obj0_object.obj")
    delete_obj_file(path)
    shutil.rmtree(os.path.join(ikea_dir, "IKEA_chair_URBAN"))

    # this are several couches in one object file
    first_path = os.path.join(ikea_dir, "IKEA_sofa_VRETA", "3b58f55ed32ceef86315023d0bef39b6_obj0_object.obj")
    split_object_according_to_groups(first_path, os.path.join(ikea_dir, "IKEA_sofa_VRETA"))
    os.remove(first_path)

    for ele in ["d1748541564ade6cfe63adf1a76042f0_obj0_object.obj", "c5e1449fc0ee6833f072f21dd9a7251_obj0_object.obj"]:
        path = os.path.join(ikea_dir, "IKEA_wardrobe_PAX", ele)
        delete_obj_file(path)

if __name__ == "__main__":
    cli()