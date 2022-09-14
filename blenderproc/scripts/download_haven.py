""" Download the haven dataset. """

from pathlib import Path
import argparse
from typing import Callable

import requests


def cli():
    """
    Command line function
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('output_folder', help="Determines where the data is going to be saved.")
    parser.add_argument('--resolution', help="Desired resolution for the hdr images. Be aware that bigger resolutions, "
                                             "take a lot of disc space.", default="2k")
    parser.add_argument('--format', help="Desired download format for the images.", default="jpg")
    parser.add_argument('--tags', nargs='+', help="Filter by asset tag.", default=None)
    parser.add_argument('--categories', nargs='+', help="Filter by asset category.", default=[])
    parser.add_argument('--types', nargs='+', help="Only download the given types",
                        default=None, choices=["textures", "hdris", "models"])
    args = parser.parse_args()

    args_output_dir = Path(args.output_folder)

    def download_file(url: str, output_path: str):
        # Download
        request = requests.get(url)
        # Write to file
        with open(output_path, "wb") as file:
            file.write(request.content)

    def download_items(item_type: str, output_dir: Path, item_download_func: Callable[[str, Path], None]):
        # Filter for type
        if args.types and item_type not in args.types:
            return

        print("Downloading " + output_dir.name + "...")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download listing
        response = requests.get(f"https://api.polyhaven.com/assets?t={item_type}"
                                f"&categories={','.join(args.categories)}")
        data = response.json()

        # Filter for tags
        if args.tags:
            data = {key: value for key, value in data.items() if
                    any(tag_list in args.tags for tag_list in value.get("tags"))}

        for i, item_id in enumerate(data.keys()):
            # Get item_id and download the item
            item_output = output_dir / item_id
            # Skip if it already exists
            if not item_output.exists() or not any(item_output.iterdir()):
                item_output.mkdir(exist_ok=True)
                print(f"({i}/{len(data)}) {item_id}")
                item_download_func(item_id, item_output)
            else:
                print(f"({i}/{len(data)}) Skipping {item_id} as it already exists")

    def download_texture(item_id: str, output_dir: Path):
        request = requests.get(f"https://api.polyhaven.com/files/{item_id}")
        data = request.json()

        # Go over all available texture types
        for key in data.keys():
            # Filter out the ones we need
            if key in ["AO", "Displacement", "Diffuse", "rough_ao", "nor_gl", "Rough"]:
                # Check resolution is available
                if args.resolution not in data[key]:
                    print(f"Skipping {key} texture {item_id} as the desired resolution is not available.")
                    continue

                # Check format is available
                if args.format not in data[key][args.resolution]:
                    print(f"Skipping {key} texture {item_id} as the desired format is not available.")
                    continue

                # Download image
                download_url = data[key][args.resolution][args.format]["url"]
                download_file(download_url, output_dir / download_url.split("/")[-1])

    def download_hdri(item_id: str, output_dir: Path):
        # Collect metadata to hdri
        request = requests.get(f"https://api.polyhaven.com/files/{item_id}")
        data = request.json()

        # Check resolution is available
        if args.resolution not in data["hdri"]:
            print(f"Skipping hdri {item_id} as the desired resolution is not available.")
            return

        # Download hdri
        download_url = data["hdri"][args.resolution]["hdr"]["url"]
        download_file(download_url, output_dir / download_url.split("/")[-1])

    def download_model(item_id: str, output_dir: Path):
        # Collect metadata to model
        request = requests.get(f"https://api.polyhaven.com/files/{item_id}")
        data = request.json()

        # Check resolution is available
        if args.resolution not in data["blend"]:
            print(f"Skipping model {item_id} as the desired resolution is not available.")
            return

        # Download blend file
        blend_data = data["blend"][args.resolution]["blend"]
        download_file(blend_data["url"], output_dir / blend_data["url"].split("/")[-1])

        # Download textures
        for texture_path, texture_data in blend_data["include"].items():
            destination = output_dir / texture_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            download_file(texture_data["url"], destination)

    download_items("textures", args_output_dir / "textures", download_texture)
    download_items("hdris", args_output_dir / "hdris", download_hdri)
    download_items("models", args_output_dir / "models", download_model)


if __name__ == "__main__":
    cli()
