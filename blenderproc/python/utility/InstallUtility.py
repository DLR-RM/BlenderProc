""" Provides functions to install BlenderProc. """

import getpass
import os
import tarfile
from os.path import join
import subprocess
import shutil
from sys import platform, version_info
import ssl
from platform import machine
from typing import Union, Tuple

if version_info.major == 3:
    from urllib.request import urlretrieve, build_opener, install_opener
    from urllib.error import URLError
else:
    from urllib import urlretrieve, build_opener, install_opener
    import contextlib

# pylint: disable=wrong-import-position
from blenderproc.python.utility.SetupUtility import SetupUtility
# pylint: enable=wrong-import-position


class InstallUtility:
    """
    This class provides functions to install BlenderProc and set up the correct environment
    """

    @staticmethod
    def determine_blender_install_path(used_args: "argparse.NameSpace") -> Union[str, str]:
        """ Determines the path of the blender installation

        :param used_args: The given command line arguments.
        :return:
               - The path to an already existing blender installation that should be used, otherwise None
               - The path to where blender should be installed.
        """
        custom_blender_path = used_args.custom_blender_path
        blender_install_path = used_args.blender_install_path

        # If no blender install path is given set it to /home_local/<env:USER>/blender/ per default
        if blender_install_path is None:
            user_name = getpass.getuser()
            blender_install_path = os.path.join("/home_local", user_name, "blender")
        return custom_blender_path, blender_install_path

    @staticmethod
    def make_sure_blender_is_installed(custom_blender_path: str, blender_install_path: str,
                                       reinstall_blender: bool = False) -> Tuple[str, str]:
        """ Make sure blender is installed.

        :param custom_blender_path: The path to an already existing blender installation that should
                                    be used, otherwise None.
        :param blender_install_path: The path to where blender should be installed.
        :param reinstall_blender: If True, blender will be forced to reinstall.
        :return:
               - The path to the blender binary.
               - The major version of the blender installation.
        """
        # If blender should be downloaded automatically
        if custom_blender_path is None:
            # Determine path where blender should be installed
            if blender_install_path is not None:
                blender_install_path = os.path.expanduser(blender_install_path)
                if blender_install_path.startswith("/home_local") and not os.path.exists("/home_local"):
                    user_name = getpass.getuser()
                    home_path = os.getenv("USERPROFILE") if platform == "win32" else os.getenv("HOME")
                    print(f"Warning: Changed install path from {join('/home_local', user_name)}... to {home_path}..., "
                          f"there is no /home_local/ on this machine.")
                    # Replace the seperator from '/' to the os-specific one
                    # Since all example config files use '/' as seperator
                    blender_install_path = blender_install_path.replace(os.path.join("/home_local", user_name),
                                                                        home_path, 1)
                    blender_install_path = blender_install_path.replace('/', os.path.sep)
            else:
                blender_install_path = "blender"

            # Determine configured version
            # right new only support blender-3.5.1
            major_version = "3.5"
            minor_version = "1"
            blender_version = f"blender-{major_version}.{minor_version}"
            if platform in ["linux", "linux2"]:
                blender_version += "-linux-x64"
                blender_path = os.path.join(blender_install_path, blender_version)
            elif platform == "darwin":
                # check if the current mac uses an Intel x86 processor
                if "x86" in machine():
                    blender_version += "-macos-x64"
                else:
                    # or an Apple Silicon
                    blender_version += "-macos-arm64"
                blender_install_path = os.path.join(blender_install_path, blender_version)
                blender_path = os.path.join(blender_install_path, "Blender.app")
            elif platform == "win32":
                blender_version += "-windows-x64"
                blender_install_path = os.path.join(blender_install_path, blender_version)
                # After unpacking there is another subfolder named blender_version
                blender_path = os.path.join(blender_install_path, blender_version)
            else:
                raise RuntimeError(f"This system is not supported yet: {platform}")

            # If forced reinstall is demanded, remove existing files
            if os.path.exists(blender_path) and reinstall_blender:
                print("Removing existing blender installation")
                shutil.rmtree(blender_path)

            # Download blender if it not already exists
            if not os.path.exists(blender_path):
                if version_info.major != 3:
                    try:
                        # pylint: disable=import-outside-toplevel
                        import lzma
                        # pylint: enable=import-outside-toplevel
                    except ImportError as e:
                        print("For decompressing \".xz\" files in python 2.x is it necessary to use lzma")
                        raise e  # from import lzma -> pip install --user pyliblzma
                used_url = "https://download.blender.org/release/Blender" + major_version + "/" + blender_version
                if platform in ["linux", "linux2"]:
                    url = used_url + ".tar.xz"
                elif platform == "darwin":
                    url = used_url + ".dmg"
                elif platform == "win32":
                    url = used_url + ".zip"
                else:
                    raise RuntimeError(f"This system is not supported yet: {platform}")
                
                # setting the default header, else the server does not allow the download
                opener = build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                install_opener(opener)

                try:
                    try:
                        # pylint: disable=import-outside-toplevel
                        import progressbar
                        # pylint: enable=import-outside-toplevel
                        class DownloadProgressBar:
                            """
                            Download progress bar, uses the progressbar library to display a progressbar during download
                            """
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
                except URLError as e:
                    if platform == "win32":
                        # on windows this is a known problem that the ssl certificates doesn't properly work
                        # deactivate the ssl check
                        if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
                                getattr(ssl, '_create_unverified_context', None)):
                            # pylint: disable=protected-access
                            ssl._create_default_https_context = ssl._create_unverified_context
                            # pylint: enable=protected-access
                        file_tmp = urlretrieve(url, None)[0]
                    else:
                        raise e
                if platform in ["linux", "linux2"]:
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
                    # pylint: disable=consider-using-with
                    # installing the blender app by mounting it and extracting the information
                    subprocess.Popen([f"hdiutil attach {os.path.join(blender_install_path, blender_version + '.dmg')}"],
                                     shell=True).wait()
                    subprocess.Popen([f'cp -r {os.path.join("/", "Volumes", "Blender", "Blender.app")} '
                                      f'{blender_install_path}'], shell=True).wait()
                    subprocess.Popen([f'diskutil unmount {os.path.join("/", "Volumes", "Blender")}'], shell=True)
                    # removing the downloaded image again
                    subprocess.Popen([f'rm {os.path.join(blender_install_path, blender_version + ".dmg")}'],
                                     shell=True).wait()
                    # pylint: enable=consider-using-with
                    # add Blender.app path to it
                elif platform == "win32":
                    SetupUtility.extract_file(blender_install_path, file_tmp)
                # rename the blender folder to better fit our existing scheme
                for folder in os.listdir(blender_install_path):
                    if os.path.isdir(os.path.join(blender_install_path, folder)) and \
                            folder.startswith(f"blender-{major_version}.{minor_version}"):
                        os.rename(os.path.join(blender_install_path, folder),
                                  os.path.join(blender_install_path, blender_version))
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
                raise RuntimeError("Could not determine major blender version")

        print("Using blender in " + blender_path)

        # Run script
        if platform in ["linux", "linux2"]:
            blender_run_path = os.path.join(blender_path, "blender")
        elif platform == "darwin":
            blender_run_path = os.path.join(blender_path, "Contents", "MacOS", "Blender")
        elif platform == "win32":
            blender_run_path = os.path.join(blender_path, "blender")
        else:
            raise RuntimeError(f"This system is not supported yet: {platform}")

        return blender_run_path, major_version
