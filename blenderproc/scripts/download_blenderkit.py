from sys import version_info
from urllib.error import HTTPError

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import urllib.request, json
from urllib.request import urlretrieve, build_opener, install_opener, urlopen
from pathlib import Path
import uuid
import argparse

def download_blendkit_assets(asset_types, output_dir):
    output_dir = Path(output_dir)
    assets = {}
    for asset_type in asset_types:
        page = 1
        print("Downloading {} assets".format(asset_type))
        while True:
            print("Download metadata: page {}".format(page))
            try:
                with urllib.request.urlopen("https://www.blenderkit.com/api/v1/search/?query=asset_type:{}+order:_score+is_free:True&addon_version=1.0.30&page={}".format(asset_type, str(page))) as url:
                    data = json.loads(url.read().decode())
                    # Extract results
                    assets.setdefault(asset_type, []).extend(data["results"])
            except HTTPError as e:
                if e.code == 404:
                    # We reached the end
                    break
                else:
                    raise
            # Goto next page
            page += 1

        total_assets = len(assets.setdefault(asset_type, []))
        print("Retrieved metadata for {} assets".format(total_assets))

        # Create ouput directory
        blenderkit_mat_dir = output_dir / ''.join([asset_type, 's'])
        blenderkit_mat_dir.mkdir(exist_ok=True, parents=True)
        # Create a random scene uuid which is necessary for downloading files
        scene_uuid = str(uuid.uuid4())
        # Set temp path for downloading. This allows clean stop and continue of the script
        temp_path = blenderkit_mat_dir / "temp.blend"

        # setting the default header, else the server does not allow the download
        opener = build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        install_opener(opener)

        for i, asset in enumerate(assets.setdefault(asset_type, [])):
            # Check if asset has already been downloaded
            output_path = blenderkit_mat_dir / (asset["id"] + ".blend")
            if output_path.exists():
                print("Skipping asset: {} of {}/{}".format(asset["id"], i, total_assets))
                continue

            print("Download asset: {} of {}/{}".format(asset["id"], i, total_assets))

            # Try to find url to blend file
            download_url = None
            for file in asset["files"]:
                if file["fileType"] == "blend":
                    if download_url is not None:
                        print("Warning: asset " + asset["id"] + " has more than one blend file in downloads.")
                    download_url = file["downloadUrl"]

            if download_url is None:
                print("Warning: asset " + asset["id"] + " has no blend file in downloads.")
                continue

            # Download metadata for blend file
            with urllib.request.urlopen(download_url + "?scene_uuid=" + scene_uuid) as url:
                data = json.loads(url.read().decode())
                # Extract actual download path
                file_path = data["filePath"]
                # Download the file
                urlretrieve(file_path, str(temp_path))
                temp_path.rename(output_path)


def cli():
    parser = argparse.ArgumentParser("Downloads materials and models from blenderkit")
    parser.add_argument('output_dir', help="Determines where the data is going to be saved")
    parser.add_argument('--asset_types', nargs="+", help="Which type of assets to download", default=["material", "model"], choices=["material", "model"])
    args = parser.parse_args()

    download_blendkit_assets(args.asset_types, args.output_dir)

if __name__ == "__main__":
    cli()