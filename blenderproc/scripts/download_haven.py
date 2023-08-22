""" Download the haven dataset. """

from pathlib import Path
import argparse
from typing import Callable
import concurrent.futures
from multiprocessing import cpu_count
import requests
from progressbar import ProgressBar, Percentage, Bar, ETA, AdaptiveETA


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
    parser.add_argument('--threads', nargs='?', type=int, help="How many threads to use for downloading", default=4)
    parser.add_argument('--types', nargs='+', help="Only download the given types",
                        default=None, choices=["textures", "hdris", "models"])
    args = parser.parse_args()
    args_output_dir = Path(args.output_folder)

    args_max_workers = min(args.threads, cpu_count())


    def download_file(url: str, output_path: str):
        # Download
        request = requests.get(url, timeout=30)
        # Write to file
        with open(output_path, "wb") as file:
            file.write(request.content)

    def download_items(item_type: str, output_dir: Path, item_download_func: Callable[[str, Path], None]):
        # Filter for type
        if args.types and item_type not in args.types:
            return

        print("Preparing download of\t" + output_dir.name )
        output_dir.mkdir(parents=True, exist_ok=True)

        # Download listing
        response = requests.get(f"https://api.polyhaven.com/assets?t={item_type}"
                                f"&categories={','.join(args.categories)}", timeout=30)
        data = response.json()

        # Filter for tags
        if args.tags:
            data = {key: value for key, value in data.items() if
                    any(tag_list in args.tags for tag_list in value.get("tags"))}

        # Helper function for filter
        def item_file_exists(item_id):
            item_output: Path = output_dir / item_id
            return not item_output.exists() or not any(item_output.iterdir())

        # Filter to only fetch files not in directory
        missing_item_ids = list(filter(item_file_exists, map(lambda item_id: item_id, data.keys())))

        # Skip download if no items are missing
        if not missing_item_ids:
            print("Skipping download of\t" + output_dir.name + " All files exist")
            return
        print("Starting download of\t" + output_dir.name )

        # Start threadpool to download
        with concurrent.futures.ThreadPoolExecutor(max_workers= args_max_workers) as executor:
            # Create a list of futures
            futures = []
            for item_id in missing_item_ids:
                item_output: Path = output_dir / item_id
                item_output.mkdir(exist_ok=True)
                futures.append(executor.submit(item_download_func, item_id, item_output))

            # Initialize progress bar
            widgets = [Percentage(),' ', Bar(), ' ', ETA(),' ', AdaptiveETA()]
            progress = ProgressBar(widgets= widgets, maxval= len(futures))

            # Execute list of futures
            for future in progress(concurrent.futures.as_completed(futures)):
                # Check for any exceptions in the threads
                # pylint: disable=broad-exception-caught
                try:
                    future.result()
                except Exception as exc:
                    print(f"Thread generated an exception: {exc}")
                # pylint: enable=broad-exception-caught



    def download_texture(item_id: str, output_dir: Path):
        request = requests.get(f"https://api.polyhaven.com/files/{item_id}", timeout=30)
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
        request = requests.get(f"https://api.polyhaven.com/files/{item_id}", timeout=30)
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
        request = requests.get(f"https://api.polyhaven.com/files/{item_id}", timeout=30)
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
