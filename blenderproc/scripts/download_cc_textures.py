import shutil
from sys import version_info, path

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import os
import json
import requests
import argparse
from pathlib import Path

from blenderproc.python.utility.SetupUtility import SetupUtility


def cli():
    parser = argparse.ArgumentParser("Downloads textures from cc0textures.com")
    parser.add_argument('output_dir', help="Determines where the data is going to be saved.")
    args = parser.parse_args()

    # setting the default header, else the server does not allow the download
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    cc_texture_dir = Path(args.output_dir)
    if not cc_texture_dir.exists():
        os.makedirs(cc_texture_dir)

    # until all download files have been found
    # this loop is necessary as the server only allows downloading the info for 100 materials at once
    current_offset = 0
    data = {}
    while True:
        offset_size = 100
        # download the json file, which contains all information
        json_url = f"https://ambientcg.com/api/v2/full_json?include=downloadData&limit={offset_size}" \
                   f"&offset={current_offset}&type=material"
        json_file_path = cc_texture_dir / f"full_info_{current_offset}.json"
        request = requests.get(json_url, headers=headers)
        with json_file_path.open("wb") as file:
            file.write(request.content)
        with json_file_path.open("r") as file:
            json_data = json.load(file)
        current_offset += offset_size
        if "foundAssets" in json_data and len(json_data["foundAssets"]) > 0:
            for asset in json_data["foundAssets"]:
                if "downloadFolders" in asset and "default" in asset["downloadFolders"] and \
                        "downloadFiletypeCategories" in asset["downloadFolders"]["default"]:
                    current_download_dict = asset["downloadFolders"]["default"]["downloadFiletypeCategories"]
                    if "zip" in current_download_dict and "downloads" in current_download_dict["zip"]:
                        for download_attr in current_download_dict["zip"]["downloads"]:
                            if "attribute" in download_attr and download_attr["attribute"] == "2K-JPG":
                                data[asset["assetId"]] = (
                                    download_attr["fullDownloadPath"], download_attr["zipContent"])
                    else:
                        print(f"No zip or downloads found for asset: {asset['assetId']}")
                else:
                    print(f"No downloadFolders or default or downloadFiletypeCategories found for asset: "
                          f"{asset['assetId']}")
        else:
            break
    excluding_list = ["sign", "roadlines", "manhole", "backdrop", "foliage", "TreeEnd", "TreeStump",
                      "3DBread", "3DApple", "FlowerSet", "FoodSteps", "PineNeedles", "Grate",
                      "PavingEdge", "Painting", "RockBrush", "WrinklesBrush", "Sticker", "3DRock"]

    # download each asset and create a folder for it (unpacking + deleting the zip included)
    for index, (asset, content) in enumerate(data.items()):
        # first check if the element should be skipped
        do_not_use = False
        for exclude_element in excluding_list:
            if asset.lower().startswith(exclude_element.lower()):
                do_not_use = True
                break
        if do_not_use:
            continue

        link, zip_assets = content
        # check if the download has already happened
        download_assets = True
        current_folder = cc_texture_dir / asset
        if not current_folder.exists():
            os.makedirs(current_folder)
        else:
            files_in_asset_folder = [file_path.name for file_path in current_folder.glob("*")]
            delete_folder = False
            for zip_asset in zip_assets:
                if zip_asset not in files_in_asset_folder:
                    delete_folder = True
                    break
            if delete_folder:
                print(f"Redownload the asset: {asset}, not all files are present after download")
                # remove folder and create it again
                shutil.rmtree(current_folder)
                os.makedirs(current_folder)
            else:
                download_assets = False

        if download_assets:
            # the asset should be downloaded and has not been downloaded yet
            print(f"Download asset: {asset} of {index}/{len(data)}")
            response = requests.get(link, headers=headers)
            SetupUtility.extract_from_response(current_folder, response)

    print(f"Done downloading textures, saved in {cc_texture_dir}")


if __name__ == "__main__":
    cli()
