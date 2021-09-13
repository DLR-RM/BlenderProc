import argparse
import os
import tarfile
from os.path import join
import subprocess
import shutil
import signal
import sys
from sys import platform, version_info

if version_info.major == 3:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve
    import contextlib

import uuid
from blenderproc.python.modules.utility.ConfigParser import ConfigParser
from blenderproc.python.utility.SetupUtility import SetupUtility

class InstallUtility:

    @staticmethod
    def determine_blender_install_path(is_config, args):
        if is_config:
            config_parser = ConfigParser()
            config = config_parser.parse(args.file, args.args, False)  # Don't parse placeholder args in batch mode.
            setup_config = config["setup"]
            custom_blender_path = setup_config["custom_blender_path"] if "custom_blender_path" in setup_config else args.custom_blender_path
            blender_install_path = setup_config["blender_install_path"] if "blender_install_path" in setup_config else args.blender_install_path
        else:
            custom_blender_path = args.custom_blender_path
            blender_install_path = args.blender_install_path

            # If no blender install path is given set it to /home_local/<env:USER>/blender/ per default
            if blender_install_path is None:
                blender_install_path = os.path.join("/home_local", os.getenv("USERNAME") if platform == "win32" else os.getenv("USER"), "blender")
        return custom_blender_path, blender_install_path
    
    @staticmethod
    def make_sure_blender_is_installed(custom_blender_path, blender_install_path, reinstall_blender):

        # If blender should be downloaded automatically
        if custom_blender_path is None:
            # Determine path where blender should be installed
            if blender_install_path is not None:
                blender_install_path = os.path.expanduser(blender_install_path)
                if blender_install_path.startswith("/home_local") and not os.path.exists("/home_local"):
                    user_name = os.getenv("USERNAME") if platform == "win32" else os.getenv("USER")
                    home_path = os.getenv("USERPROFILE") if platform == "win32" else os.getenv("HOME")
                    print("Warning: Changed install path from {}... to {}..., there is no /home_local/ "
                          "on this machine.".format(join("/home_local", user_name), home_path))
                    # Replace the seperator from '/' to the os-specific one
                    # Since all example config files use '/' as seperator
                    blender_install_path = blender_install_path.replace('/'.join(["/home_local", user_name]), home_path, 1)
                    blender_install_path = blender_install_path.replace('/', os.path.sep)
            else:
                blender_install_path = "blender"

            # Determine configured version
            # right new only support blender-2.93
            major_version = "2.93"
            minor_version = "0"
            blender_version = "blender-{}.{}".format(major_version, minor_version)
            if platform == "linux" or platform == "linux2":
                blender_version += "-linux-x64"
                blender_path = os.path.join(blender_install_path, blender_version)
            elif platform == "darwin":
                blender_version += "-macos-x64"
                blender_install_path = os.path.join(blender_install_path, blender_version)
                blender_path = os.path.join(blender_install_path, "Blender.app")
            elif platform == "win32":
                blender_version += "-windows-x64"
                blender_install_path = os.path.join(blender_install_path, blender_version)
                blender_path = blender_install_path
            else:
                raise Exception("This system is not supported yet: {}".format(platform))

            # If forced reinstall is demanded, remove existing files
            if os.path.exists(blender_path) and reinstall_blender:
                print("Removing existing blender installation")
                shutil.rmtree(blender_path)

            # Download blender if it not already exists
            if not os.path.exists(blender_path):
                if version_info.major != 3:
                    try:
                        import lzma
                    except ImportError as e:
                        print("For decompressing \".xz\" files in python 2.x is it necessary to use lzma")
                        raise e  # from import lzma -> pip install --user pyliblzma
                used_url = "https://download.blender.org/release/Blender" + major_version + "/" + blender_version
                if platform == "linux" or platform == "linux2":
                    url = used_url + ".tar.xz"
                elif platform == "darwin":
                    url = used_url + ".dmg"
                elif platform == "win32":
                    url = used_url + ".zip"
                else:
                    raise Exception("This system is not supported yet: {}".format(platform))
                try:
                    import progressbar
                    class DownloadProgressBar(object):
                        def __init__(self):
                            self.pbar = None

                        def __call__(self, block_num, block_size, total_size):
                            if not self.pbar:
                                self.pbar = progressbar.ProgressBar(maxval=total_size)
                                self.pbar.start()
                            downloaded = block_num * block_size
                            if downloaded < total_size:
                                self.pbar.update(downloaded)
                            else:
                                self.pbar.finish()

                    print("Downloading blender from " + url)
                    file_tmp = urlretrieve(url, None, DownloadProgressBar())[0]
                except ImportError:
                    print("Progressbar for downloading, can only be shown, "
                          "when the python package \"progressbar\" is installed")
                    file_tmp = urlretrieve(url, None)[0]

                if platform == "linux" or platform == "linux2":
                    if version_info.major == 3:
                        SetupUtility.extract_file(blender_install_path, file_tmp, "TAR")
                    else:
                        with contextlib.closing(lzma.LZMAFile(file_tmp)) as xz:
                            with tarfile.open(fileobj=xz) as f:
                                f.extractall(blender_install_path)
                elif platform == "darwin":
                    if not os.path.exists(blender_install_path):
                        os.makedirs(blender_install_path)
                    os.rename(file_tmp, os.path.join(blender_install_path, blender_version + ".dmg"))
                    # installing the blender app by mounting it and extracting the information
                    subprocess.Popen(["hdiutil attach {}".format(os.path.join(blender_install_path, blender_version + ".dmg"))],
                                     shell=True).wait()
                    subprocess.Popen(
                        ["cp -r {} {}".format(os.path.join("/", "Volumes", "Blender", "Blender.app"), blender_install_path)],
                        shell=True).wait()
                    subprocess.Popen(["diskutil unmount {}".format(os.path.join("/", "Volumes", "Blender"))], shell=True)
                    # removing the downloaded image again
                    subprocess.Popen(["rm {}".format(os.path.join(blender_install_path, blender_version + ".dmg"))], shell=True).wait()
                    # add Blender.app path to it
                elif platform == "win32":
                    SetupUtility.extract_file(blender_install_path, file_tmp)
                # rename the blender folder to better fit our existing scheme
                for folder in os.listdir(blender_install_path):
                    if os.path.isdir(os.path.join(blender_install_path, folder)) and folder.startswith("blender-" + major_version):
                        os.rename(os.path.join(blender_install_path, folder), os.path.join(blender_install_path, blender_version))
        else:
            blender_path = os.path.expanduser(custom_blender_path)

            # Try to get major version of given blender installation
            major_version = None
            for sub_dir in os.listdir(blender_path):
                # Search for the subdirectory which has the major version as its name
                if os.path.isdir(os.path.join(blender_path, sub_dir)) and sub_dir.replace(".", "").isdigit():
                    major_version = sub_dir
                    break

            if major_version is None:
                raise Exception("Could not determine major blender version")

        print("Using blender in " + blender_path)

        # Run script
        if platform == "linux" or platform == "linux2":
            blender_run_path = os.path.join(blender_path, "blender")
        elif platform == "darwin":
            blender_run_path = os.path.join(blender_path, "Contents", "MacOS", "Blender")
        elif platform == "win32":
            blender_run_path = os.path.join(blender_install_path, "blender-windows64", "blender")
        else:
            raise Exception("This system is not supported yet: {}".format(platform))

        return blender_run_path