
from sys import version_info
from urllib.error import HTTPError

if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import urllib.request, json
from urllib.request import urlretrieve, build_opener, install_opener
from pathlib import Path
import uuid

assets = []
page = 1
while True:
    print("Download metadata: page {}".format(page))

    # Download one page of metadata
    try:
        with urllib.request.urlopen("https://www.blenderkit.com/api/v1/search/?query=asset_type:material+order:_score+is_free:True&addon_version=1.0.30&page=" + str(page)) as url:
            data = json.loads(url.read().decode())
            # Extract results
            assets.extend(data["results"])
    except HTTPError as e:
        if e.code == 404:
            # We reached the end
            break
        else:
            raise
    # Goto next page
    page += 1

print("Retrieved metadata for " + str(len(assets)) + " assets")

# Create ouput directory
current_dir = Path(__file__).parent
blenderkit_mat_dir = current_dir / ".." / "resources" / "blenderkit" / "materials"
blenderkit_mat_dir.mkdir(exist_ok=True, parents=True)
# Create a random scene uuid which is necessary for downloading files
scene_uuid = str(uuid.uuid4())
# Set temp path for downloading. This allows clean stop and continue of the script
temp_path = blenderkit_mat_dir / "temp.blend"

# setting the default header, else the server does not allow the download
opener = build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
install_opener(opener)

for i, asset in enumerate(assets):
    # Check if asset has already been downloaded
    output_path = blenderkit_mat_dir / (asset["id"] + ".blend")
    if output_path.exists():
        print("Skipping asset: {} of {}/{}".format(asset["id"], i, len(assets)))
        continue

    print("Download asset: {} of {}/{}".format(asset["id"], i, len(assets)))

    # Try to find url to blend file
    download_url = None
    for file in asset["files"]:
        if file["fileType"] == "blend":
            if download_url is not None:
                print("Warning: asset " + asset["id"] + " has more then one blend file in downloads.")
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