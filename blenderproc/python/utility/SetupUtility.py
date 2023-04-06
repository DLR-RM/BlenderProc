""" Ensures that all necessary pip packages are installed in the blender environment. """

import os
import sys
import tarfile
from sys import platform
import subprocess
import importlib
from io import BytesIO
import zipfile
import uuid
from typing import List, Optional, Union, Dict
import json

import requests

from blenderproc.python.utility.DefaultConfig import DefaultConfig


class SetupUtility:
    """
    Setup class, ensures that all necessary pip packages are there
    """
    # Remember already installed packages, so we do not have to call pip freeze multiple times
    installed_packages: Optional[Dict[str, str]] = None
    package_list_is_from_cache = False
    main_setup_called = False

    @staticmethod
    def setup(user_required_packages: Optional[List[str]] = None, blender_path: Optional[str] = None,
              major_version: Optional[str] = None, reinstall_packages: bool = False,
              debug_args: Optional[List[str]] = None) -> List[str]:
        """ Sets up the python environment.

        - Makes sure all required pip packages are installed
        - Prepares the given sys.argv

        :param user_required_packages: A list of python packages that are additionally necessary to execute the
                                       python script.
        :param blender_path: The path to the blender installation. If None, it is determined automatically based on
                             the current python env.
        :param major_version: The version number of the blender installation. If None, it is determined automatically
                              based on the current python env.
        :param reinstall_packages: Set to true, if all python packages should be reinstalled.
        :param debug_args: Can be used to overwrite sys.argv in debug mode.
        :return: List of sys.argv after removing blender specific commands
        """
        packages_path = SetupUtility.setup_pip(user_required_packages, blender_path, major_version, reinstall_packages)

        if not SetupUtility.main_setup_called:
            SetupUtility.main_setup_called = True
            sys.path.append(packages_path)
            is_debug_mode = "--background" not in sys.argv

            # Setup temporary directory
            if is_debug_mode:
                SetupUtility.setup_utility_paths("examples/debugging/temp")
            else:
                SetupUtility.setup_utility_paths(sys.argv[sys.argv.index("--") + 2])

            # Only prepare args in non-debug mode (In debug mode the arguments are already ready to use)
            if not is_debug_mode:
                # Cut off blender specific arguments
                sys.argv = sys.argv[sys.argv.index("--") + 1:sys.argv.index("--") + 2] + \
                           sys.argv[sys.argv.index("--") + 3:]
            elif debug_args is not None:
                sys.argv = ["debug"] + debug_args

        return sys.argv

    @staticmethod
    def setup_utility_paths(temp_dir: str):
        """ Set utility paths: Temp dir and working dir.

        :param temp_dir: Path to temporary directory where Blender saves output. Default is shared memory.
        """
        # pylint: disable=import-outside-toplevel,cyclic-import
        from blenderproc.python.utility.Utility import Utility, resolve_path
        # pylint: enable=import-outside-toplevel,cyclic-import

        Utility.temp_dir = resolve_path(temp_dir)
        os.makedirs(Utility.temp_dir, exist_ok=True)

    @staticmethod
    def determine_python_paths(blender_path: Optional[str], major_version: Optional[str]) -> Union[str, str, str, str]:
        """ Determines python binary, custom pip packages and the blender pip packages path.

        :param blender_path: The path to the blender main folder.
        :param major_version: The major version string of the blender installation.
        :return:
              - The path to the python binary of the blender installation
              - The path to the directory containing custom pip packages installed by BlenderProc
              - The path to the directory containing pip packages installed by blender.
        """
        # If no bleneder path is given, determine it based on sys.executable
        if blender_path is None:
            blender_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", ".."))
            major_version = os.path.basename(os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..")))

        # Based on the OS determined the three paths
        current_python_version = "python3.10"
        if platform in ["linux", "linux2"]:
            python_bin_folder = os.path.join(blender_path, major_version, "python", "bin")
            python_bin = os.path.join(python_bin_folder, current_python_version)
            packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
            packages_import_path = os.path.join(packages_path, "lib", current_python_version, "site-packages")
            pre_python_package_path = os.path.join(blender_path, major_version, "python", "lib",
                                                   current_python_version, "site-packages")
        elif platform == "darwin":
            python_bin_folder = os.path.join(blender_path, "..", "Resources", major_version, "python", "bin")
            python_bin = os.path.join(python_bin_folder, current_python_version)
            packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
            packages_import_path = os.path.join(packages_path, "lib", current_python_version, "site-packages")
            pre_python_package_path = os.path.join(blender_path, "..", "Resources", major_version, "python",
                                                   "lib", current_python_version, "site-packages")
        elif platform == "win32":
            python_bin_folder = os.path.join(blender_path, major_version, "python", "bin")
            python_bin = os.path.join(python_bin_folder, "python")
            packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
            packages_import_path = os.path.join(packages_path, current_python_version.replace(".", "").capitalize(),
                                                "site-packages")
            pre_python_package_path = os.path.join(blender_path, major_version, "python", "lib", "site-packages")
        else:
            raise RuntimeError(f"This system is not supported yet: {platform}")

        return python_bin, packages_path, packages_import_path, pre_python_package_path

    @staticmethod
    def setup_pip(user_required_packages: Optional[List[str]] = None, blender_path: Optional[str] = None,
                  major_version: Optional[str] = None, reinstall_packages: bool = False,
                  use_custom_package_path: bool = True, install_default_packages: bool = True) -> str:
        """
        Makes sure the given user required and the general required python packages are installed in the BlenderProc env

        At the first run all installed packages are collected via pip freeze.
        If a pip packages is already installed, it is skipped.

        :param user_required_packages: A list of pip packages that should be installed. The version number can be
                                       specified via the usual == notation.
        :param blender_path: The path to the blender installation.
        :param major_version: The version number of the blender installation.
        :param reinstall_packages: Set to true, if all python packages should be reinstalled.
        :param use_custom_package_path: If True, the python packages are installed into a custom folder, separate
                                        from blenders own python packages.
        :param install_default_packages: If True, general required python packages are made sure to be installed.
        :return: Returns the path to the directory which contains all custom installed pip packages.
        """
        required_packages = []
        # Only install general required packages on first setup_pip call
        if SetupUtility.installed_packages is None and install_default_packages:
            required_packages += DefaultConfig.default_pip_packages
        if user_required_packages is not None:
            required_packages += user_required_packages

        if reinstall_packages:
            raise ValueError("The reinstall package mode is not supported right now!")

        result = SetupUtility.determine_python_paths(blender_path, major_version)
        python_bin, packages_path, packages_import_path, pre_python_package_path = result

        # Init pip
        SetupUtility._ensure_pip(python_bin, packages_path, packages_import_path, pre_python_package_path)

        # If the list of installed packages was read from cache
        if SetupUtility.package_list_is_from_cache:
            # Check if there would be any pip package updates based on the cache
            found_package_to_install = SetupUtility._pip_install_packages(required_packages, python_bin,
                                                                          packages_path, dry_run=True)
            # If yes, reload the list of installed packages
            if found_package_to_install:
                SetupUtility._ensure_pip(python_bin, packages_path, packages_import_path,
                                         pre_python_package_path, force_update=True)

        packages_were_installed = SetupUtility._pip_install_packages(required_packages, python_bin,
                                                                     packages_path,
                                                                     use_custom_package_path=use_custom_package_path)

        # Make sure to update the pip package list cache, if it does not exist or changes have been made
        cache_path = os.path.join(packages_path, "installed_packages_cache_v2.json")
        if packages_were_installed or not os.path.exists(cache_path):
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(SetupUtility.installed_packages, f)

        # If packages were installed, invalidate the module cache, s.t. the new modules can be imported right away
        if packages_were_installed:
            importlib.invalidate_caches()
        return packages_import_path

    @staticmethod
    def _pip_install_packages(required_packages, python_bin, packages_path, reinstall_packages: bool = False,
                              dry_run: bool = False, use_custom_package_path: bool = True) -> bool:
        """ Installs the list of given pip packages in the given python environment.

        :param required_packages: A list of pip packages that should be installed. The version number can be
                                  specified via the usual == notation.
        :param python_bin: Path to python binary.
        :param packages_path: Path where our pip packages should be installed
        :param reinstall_packages: Set to true, if all python packages should be reinstalled.
        :param dry_run: If true, nothing will be installed, and it will only be checked whether there are
                        any potential packages to update/install.
        :param use_custom_package_path: If True, the python packages are installed into a custom folder,
                                        separate from blenders own python packages.
        :return: Returns True, if any packages were update/installed or - if dry_run=True - if there are any potential
                 packages to update/install.
        """
        # Install all packages
        packages_were_installed = False
        for package in required_packages:
            # If -f (find_links) flag for pip install in required package set find_link = link to parse
            find_link = None

            # Extract name and target version
            if "==" in package:
                package_name, package_version = package.lower().split('==')
                if ' -f ' in package_version:
                    find_link = package_version.split(' -f ')[1].strip()
                    package_version = package_version.split(' -f ')[0].strip()
            else:
                package_name, package_version = package.lower(), None

            if package_name == "opencv-python":
                raise RuntimeError("Please use opencv-contrib-python instead of opencv-python, as having both "
                                   "packages installed in the same environment can lead to complications.")

            # If the package is given via git, extract package name from url
            if package_name.startswith("git+"):
                # Extract part after last slash
                package_name = package_name[package_name.rfind("/") + 1:]
                # Replace underscores with dashes as it's done by pip
                package_name = package_name.replace("_", "-")

            # Check if package is installed
            # pylint: disable=unsupported-membership-test
            already_installed = package_name in SetupUtility.installed_packages
            # pylint: enable=unsupported-membership-test

            # If version check is necessary
            if package_version is not None and already_installed:
                # Check if the correct version is installed
                # pylint: disable=unsubscriptable-object
                already_installed = package_version == SetupUtility.installed_packages[package_name]
                # pylint: enable=unsubscriptable-object

            # Only install if it's not already installed (pip would check this itself, but at first downloads the
            # requested package which of course always takes a while)
            if not already_installed or reinstall_packages:
                print(f"Installing pip package {package_name} {package_version}")
                extra_args = []
                # Set find link flag, if required
                if find_link:
                    extra_args.extend(["-f", find_link])
                    package = package_name + "==" + package_version
                # If the env var is set, disable pip cache
                if os.getenv("BLENDER_PROC_NO_PIP_CACHE", 'False').lower() in ('true', '1', 't'):
                    extra_args.append("--no-cache-dir")

                if not dry_run:
                    if use_custom_package_path:
                        extra_args.extend(["--user"])
                    # Run pip install
                    # pylint: disable=consider-using-with
                    subprocess.Popen([python_bin, "-m", "pip", "install", package, "--upgrade"] + extra_args,
                                     env=dict(os.environ, PYTHONNOUSERSITE="0", PYTHONUSERBASE=packages_path)).wait()
                    # pylint: enable=consider-using-with
                    # pylint: disable=unsupported-assignment-operation
                    SetupUtility.installed_packages[package_name] = package_version
                    # pylint: enable=unsupported-assignment-operation
                    packages_were_installed = True
                else:
                    return True

        return packages_were_installed

    @staticmethod
    def uninstall_pip_packages(package_names: List[str], blender_path: str, major_version: str):
        """ Uninstalls the given pip packages in blenders python environment.

        :param package_names: A list of pip packages that should be uninstalled.
        :param blender_path: The path to the blender main folder.
        :param major_version: The major version string of the blender installation.
        """
        # Determine python and packages paths
        python_bin, _, packages_import_path, _ = SetupUtility.determine_python_paths(blender_path, major_version)

        # Run pip uninstall
        # pylint: disable=consider-using-with
        subprocess.Popen([python_bin, "-m", "pip", "uninstall"] + package_names,
                         env=dict(os.environ, PYTHONPATH=packages_import_path)).wait()
        # pylint: enable=consider-using-with

        # Clear installed packages cache
        SetupUtility.clean_installed_packages_cache(blender_path, major_version)

    @staticmethod
    def _ensure_pip(python_bin: str, packages_path: str, packages_import_path: str,
                    pre_python_package_path: str, force_update: bool = False):
        """ Make sure pip is installed and read in the already installed packages

        :param python_bin: Path to python binary.
        :param packages_path: Path where our pip packages should be installed
        :param packages_import_path: Path to site-packages in packages_path which contains the installed packages
        :param pre_python_package_path: Path that contains blender's default pip packages
        :param force_update: If True, the installed-packages-cache will be ignored and will be recollected based
                             on the actually installed packages.
        """
        if SetupUtility.installed_packages is None:
            if not force_update:
                cache_path = os.path.join(packages_path, "installed_packages_cache_v2.json")
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        SetupUtility.installed_packages = json.load(f)
                        SetupUtility.package_list_is_from_cache = True
                    return

            SetupUtility.installed_packages = {}
            # pylint: disable=consider-using-with
            subprocess.Popen([python_bin, "-m", "ensurepip"], env=dict(os.environ, PYTHONPATH="")).wait()
            # Make sure pip is up-to-date
            subprocess.Popen([python_bin, "-m", "pip", "install", "--upgrade", "pip"],
                             env=dict(os.environ, PYTHONPATH="")).wait()
            # pylint: enable=consider-using-with

            # Make sure to not install into the default site-packages path, as this would overwrite
            # already pre-installed packages
            if not os.path.exists(packages_path):
                os.mkdir(packages_path)

            # Collect already installed packages by calling pip list (outputs: <package name>==<version>)
            installed_packages = subprocess.check_output([python_bin, "-m", "pip", "list", "--format=freeze",
                                                          f"--path={pre_python_package_path}"])
            installed_packages += subprocess.check_output([python_bin, "-m", "pip", "list", "--format=freeze",
                                                           f"--path={packages_import_path}"])

            # Split up strings into two lists (names and versions)
            installed_packages_name, installed_packages_versions = zip(*[str(line).lower().split('==')
                                                                         for line in installed_packages.splitlines()])
            installed_packages_name = [ele[2:] if ele.startswith("b'") else ele
                                       for ele in installed_packages_name]
            installed_packages_versions = [ele[:-1] if ele.endswith("'") else ele
                                           for ele in installed_packages_versions]
            SetupUtility.installed_packages = dict(zip(installed_packages_name, installed_packages_versions))
            SetupUtility.package_list_is_from_cache = False

    @staticmethod
    def clean_installed_packages_cache(blender_path, major_version):
        """ Removes the json file containing a list of all installed pip packages (if it exists).

        :param blender_path: The path to the blender main folder.
        :param major_version: The major version string of the blender installation.
        """
        _, packages_path, _, _ = SetupUtility.determine_python_paths(blender_path, major_version)
        cache_path = os.path.join(packages_path, "installed_packages_cache_v2.json")
        if os.path.exists(cache_path):
            os.remove(cache_path)

    @staticmethod
    def extract_file(output_dir: str, file: Union[str, BytesIO], mode: str = "ZIP"):
        """ Extract all members from the archive into output_dir.

        :param output_dir: The output directory that should contain the extracted files.
        :param file: The path to the archive which should be extracted.
        :param mode: The type of the given file, has to be in ["TAR", "ZIP"]
        """
        try:
            if mode.lower() == "zip":
                with zipfile.ZipFile(file) as tar:
                    tar.extractall(str(output_dir))
            elif mode.lower() == "tar":
                with tarfile.open(file) as tar:
                    tar.extractall(str(output_dir))
            else:
                raise RuntimeError(f"No such mode: {mode}")

        except (IOError, zipfile.BadZipfile) as e:
            print(f"Bad zip file given as input. {e}")
            raise e

    @staticmethod
    def extract_from_response(output_dir: str, response: requests.Response):
        """ Extract all members from the archive to output_dir

        :param output_dir: the dir to zip file extract to
        :param response: the response to a requested url that contains a zip file
        """
        file = BytesIO(response.content)
        SetupUtility.extract_file(output_dir, file)

    @staticmethod
    def check_if_setup_utilities_are_at_the_top(path_to_run_file: str):
        """
        Checks if the given python scripts has at the top an import to SetupUtility, if not an
        exception is thrown. With an explanation that each python script has to start with SetupUtility.

        :param path_to_run_file: path to the used python script
        """
        if os.path.exists(path_to_run_file):
            with open(path_to_run_file, "r", encoding="utf-8") as file:
                text = file.read()
                lines = [l.strip() for l in text.split("\n")]
                lines = [l for l in lines if l and not l.startswith("#")]
                for index, line in enumerate(lines):
                    if "import blenderproc" in line or "from blenderproc" in line:
                        return
                    code = "\n".join(lines[:index + 2])
                    raise RuntimeError(f'The given script "{path_to_run_file}" does not have a blenderproc '
                                       f'import at the top! Make sure that is the first thing you import, as '
                                       f'otherwise the import of third-party packages installed in the '
                                       f'blender environment will fail.\n'
                                       f'Your code:\n#####################\n{code}\n"'
                                       f'"####################\nReplaces this with:\n"'
                                       f'"import blenderproc as bproc"')
        else:
            raise RuntimeError(f"The given run script does not exist: {path_to_run_file}")

    @staticmethod
    def determine_temp_dir(given_temp_dir: str) -> str:
        """ Finds and creates a temporary directory.

        On linux the temp dir is per default placed in /dev/shm or /tmp.
        The name of the created temp dir contains a uuid, so multiple BlenderProc processes
        can run on one system.

        :param given_temp_dir: A directory inside which the temp dir should be created
        :return: The path to the created temp dir.
        """
        # Determine perfect temp dir
        if given_temp_dir is None:
            if sys.platform != "win32":
                if os.path.exists("/dev/shm"):
                    temp_dir = "/dev/shm"
                else:
                    temp_dir = "/tmp"
            else:
                temp_dir = os.getenv("TEMP")
        else:
            temp_dir = given_temp_dir
        # Generate unique directory name in temp dir
        temp_dir = os.path.join(temp_dir, "blender_proc_" + str(uuid.uuid4().hex))
        # Create the temp dir
        print("Using temporary directory: " + temp_dir)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir
