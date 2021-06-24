import argparse
import json
import os
import glob

# This script extracts all id labels used in 3D Front, as they change every few months, this can be used to
# regenerate them. Results will be saved in 3D_front_mapping_generated.csv
parser = argparse.ArgumentParser("This detects all labels which are currently used in the 3D Front dataset.")
parser.add_argument("front_folder", help="Folder path to the 3D FRONT dataset. The folder should contain the json files.")
parser.add_argument("future_folder", help="Folder path to the 3D FUTURE model dataset.")
args = parser.parse_args()

# check if the given folder paths exist
folder_path = args.front_folder
if not os.path.exists(folder_path):
    raise Exception("The given front folder path does not exist!")

model_path = args.future_folder
if not os.path.exists(model_path):
    raise Exception("The given future folder path does not exist!")

# find all json files
json_files = glob.glob(os.path.join(folder_path, "*.json"))
all_category_names = set()
not_used_models = set()

# iterate over all json files
for i, json_path in enumerate(json_files):
    # load data from json file
    with open(json_path, "r") as json_file:
        data = json.load(json_file)
    # check all furniture objects
    for ele in data["furniture"]:
        ele_folder_path = os.path.join(model_path, ele["jid"])
        obj_file = os.path.join(ele_folder_path, "raw_model.obj")
        # check if an obj file exists, a lot of them don't
        if os.path.exists(obj_file):
            if "category" in ele:
                used_obj_name = ele["category"]
            elif "title" in ele:
                used_obj_name = ele["title"]
                if "/" in used_obj_name:
                    used_obj_name = used_obj_name.split("/")[0]
            else:
                not_used_models.add(obj_file)
                continue
            if len(used_obj_name) == 0:
                not_used_models.add(obj_file)
                continue
            # add category name for each object to the set
            category_name = used_obj_name.lower()
            all_category_names.add(category_name)
    for mesh_data in data["mesh"]:
        # extract the obj name, which also is used as the category_id name
        used_obj_name = mesh_data["type"].strip()
        if used_obj_name == "":
            used_obj_name = "void"
        # add category name for each structure to the set
        category_name = used_obj_name.lower()
        all_category_names.add(category_name)
    print(f"Done with {i} of {len(json_files)}")

# this is already represented by void
if "unknown" in all_category_names:
    all_category_names.remove("unknown")
if "void" in all_category_names:
    all_category_names.remove("void")

print(f"These are all categories: {list(all_category_names)}")
print(f"There are {len(all_category_names)} categories found.")
print(f"There are {len(not_used_models)} models which have been defined but not found on disc!")

# create csv
text = ["id,name", "0,void"]
text.extend(f"{i+1},{name}" for i, name in enumerate(all_category_names))
with open(os.path.join(os.path.dirname(__file__), "3D_front_mapping_generated.csv"), "w") as file:
    file.write("\n".join(text))

print("Finished writing csv to disc!")
