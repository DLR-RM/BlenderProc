""" Download script for Matterport3D. """

from pathlib import Path
import zipfile
import subprocess
import argparse
import os


def cli():
    """
    Command line function
    """
    parser = argparse.ArgumentParser("Downloads the Matterport3D dataset")
    parser.add_argument('download_mp_script', help="Path to the download script, this script is only available after "
                                                   "accepting the Terms of Use.")
    parser.add_argument('scans_txt_path', help="Path to the scans.txt data, this file is only available after "
                                               "accepting the Terms of Use.")
    parser.add_argument('output_dir', help="Determines where the data is going to be saved.")
    args = parser.parse_args()

    data_path = Path(args.output_dir)
    data_path.mkdir(exist_ok=True)

    scan_file = Path(args.scans_txt_path)
    if not scan_file.exists():
        raise FileNotFoundError("The scans.txt file could not be found check argument.")

    with scan_file.open("r", encoding="utf-8") as file:
        current_ids = [id_val for id_val in file.read().split("\n") if id_val.strip()]

    download_mp_file = Path(args.download_mp_script).absolute()
    if not download_mp_file.exists():
        raise FileNotFoundError(f"The download_mp script could not be found: {download_mp_file}")

    for current_id in current_ids:
        # the script only works with python2, and it only downloads the matterport_mesh nothing else
        cmd = f"python2 -u {download_mp_file} -o {data_path} --id {current_id} --type matterport_mesh"
        with subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE) as pipe:
            # agree to terms of use -> was already done via e-mail
            pipe.communicate(input="agree".encode())

    for zip_file in (data_path / "v1" / "scans").glob("*/*.zip"):
        with zipfile.ZipFile(zip_file) as tar:
            tar.extractall(str(Path(zip_file.absolute()).parent))
        os.remove(zip_file)


if __name__ == "__main__":
    cli()
