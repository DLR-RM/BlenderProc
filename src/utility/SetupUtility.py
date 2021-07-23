import os
import sys
import tarfile
from sys import platform
import subprocess
import importlib
from io import BytesIO
import zipfile

class SetupUtility:

    # Remember already installed packages, so we do not have to call pip freeze multiple times
    installed_packages = None

    @staticmethod
    def setup(user_required_packages=None, blender_path=None, major_version=None, reinstall_packages=False, debug_args=None):
        """ Sets up the python environment.

        - Makes sure all required pip packages are installed
        - Prepares the given sys.argv

        :param user_required_packages: A list of python packages that are additionally necessary to execute the python script.
        :param blender_path: The path to the blender installation. If None, it is determined automatically based on the current python env.
        :param major_version: The version number of the blender installation. If None, it is determined automatically based on the current python env.
        :param reinstall_packages: Set to true, if all python packages should be reinstalled.
        :param debug_args: Can be used to overwrite sys.argv in debug mode.
        """
        packages_path = SetupUtility.setup_pip(user_required_packages, blender_path, major_version, reinstall_packages)
        sys.path.append(packages_path)

        is_debug_mode = "--background" not in sys.argv
        if is_debug_mode:
            # Delete all loaded models inside src/, as they are cached inside blender
            for module in list(sys.modules.keys()):
                if module.startswith("src") and not module == "src.utility.SetupUtility":
                    del sys.modules[module]
        
        # Setup temporary directory
        if is_debug_mode:
            SetupUtility.setup_utility_paths("examples/debugging/temp")
        else:
            SetupUtility.setup_utility_paths(sys.argv[sys.argv.index("--") + 2])
        
        # Only prepare args in non-debug mode (In debug mode the arguments are already ready to use)
        if not is_debug_mode:
            # Cut off blender specific arguments
            sys.argv = sys.argv[sys.argv.index("--") + 1:sys.argv.index("--") + 2] + sys.argv[sys.argv.index("--") + 3:]
        elif debug_args is not None:
            sys.argv = ["debug"] + debug_args
            
        return sys.argv

    @staticmethod
    def setup_utility_paths(temp_dir):
        """ Set utility paths: Temp dir and working dir.

        :param temp_dir: Path to temporary directory where Blender saves output. Default is shared memory.
        """
        from src.utility.Utility import Utility
        
        Utility.temp_dir = Utility.resolve_path(temp_dir)
        Utility.working_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        os.makedirs(Utility.temp_dir, exist_ok=True)
    
    @staticmethod
    def setup_pip(user_required_packages=None, blender_path=None, major_version=None, reinstall_packages=False):
        """ Makes sure the given user required and the general required python packages are installed in the blender proc env

        At the first run all installed packages are collected via pip freeze.
        If a pip packages is already installed, it is skipped.

        :param user_required_packages: A list of pip packages that should be installed. The version number can be specified via the usual == notation.
        :param blender_path: The path to the blender installation.
        :param major_version: The version number of the blender installation.
        :param reinstall_packages: Set to true, if all python packages should be reinstalled.
        :return: Returns the path to the directory which contains all custom installed pip packages.
        """
        # If no bleneder path is given, determine it based on sys.executable
        if blender_path is None:
            blender_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", ".."))
            major_version = os.path.basename(os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..")))

        required_packages = []
        # Only install general required packages on first setup_pip call
        if SetupUtility.installed_packages is None:
            required_packages += ["wheel", "pyyaml==5.1.2", "imageio", "gitpython"]
        if user_required_packages is not None:
            required_packages += user_required_packages

        # Install pip
        if platform == "linux" or platform == "linux2":
            python_bin_folder = os.path.join(blender_path, major_version, "python", "bin")
            python_bin = os.path.join(python_bin_folder, "python3.9")
            packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
            pre_python_package_path = os.path.join(blender_path, major_version, "python", "lib", "python3.9", "site-packages")
        elif platform == "darwin":
            python_bin_folder = os.path.join(blender_path, major_version, "python", "bin")
            python_bin = os.path.join(python_bin_folder, "python3.9")
            packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
            pre_python_package_path = os.path.join(blender_path, major_version, "python", "lib", "python3.9", "site-packages")
        elif platform == "win32":
            python_bin_folder = os.path.join(blender_path, major_version, "python", "bin")
            python_bin = os.path.join(python_bin_folder, "python")
            packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
            pre_python_package_path = os.path.join(blender_path, major_version, "python", "lib", "site-packages")
        else:
            raise Exception("This system is not supported yet: {}".format(platform))

        # Init pip
        SetupUtility._ensure_pip(python_bin, packages_path, pre_python_package_path)

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
                raise Exception("Please use opencv-contrib-python instead of opencv-python, as having both packages installed in the same environment can lead to complications.")

            # If the package is given via git, extract package name from url
            if package_name.startswith("git+"):
                # Extract part after last slash
                package_name = package_name[package_name.rfind("/") + 1:]
                # Replace underscores with dashes as its done by pip
                package_name = package_name.replace("_", "-")

            # Check if package is installed
            already_installed = package_name in SetupUtility.installed_packages

            # If version check is necessary
            if package_version is not None and already_installed:
                # Check if the correct version is installed
                already_installed = (package_version == SetupUtility.installed_packages[package_name])

                # If there is already a different version installed
                if not already_installed:
                    # Remove the old version (We have to do this manually, as we are using --target with pip install. There old version are not removed)
                    subprocess.Popen([python_bin, "-m", "pip", "uninstall", package_name, "-y"], env=dict(os.environ, PYTHONPATH=packages_path)).wait()

            # Only install if its not already installed (pip would check this itself, but at first downloads the requested package which of course always takes a while)
            if not already_installed or reinstall_packages:
                print("Installing pip package {} {}".format(package_name, package_version))
                extra_args = []
                # Set find link flag, if required
                if find_link:
                    extra_args.extend(["-f", find_link])
                    package = package_name + "==" + package_version
                # If the env var is set, disable pip cache
                if os.getenv("BLENDER_PROC_NO_PIP_CACHE", 'False').lower() in ('true', '1', 't'):
                    extra_args.append("--no-cache-dir")

                # Run pip install
                subprocess.Popen([python_bin, "-m", "pip", "install", package, "--target", packages_path, "--upgrade"] + extra_args, env=dict(os.environ, PYTHONPATH=packages_path)).wait()
                SetupUtility.installed_packages[package_name] = package_version
                packages_were_installed = True

        # If packages were installed, invalidate the module cache, s.t. the new modules can be imported right away
        if packages_were_installed:
            importlib.invalidate_caches()
        return packages_path

    @staticmethod
    def _ensure_pip(python_bin, packages_path, pre_python_package_path):
        """ Make sure pip is installed and read in the already installed packages

        :param python_bin: Path to python binary.
        :param packages_path: Path where our pip packages should be installed
        :param pre_python_package_path: Path that contains blender's default pip packages
        """
        if SetupUtility.installed_packages is None:
            subprocess.Popen([python_bin, "-m", "ensurepip"], env=dict(os.environ, PYTHONPATH="")).wait()
            # Make sure pip is up-to-date
            subprocess.Popen([python_bin, "-m", "pip", "install", "--upgrade", "pip"], env=dict(os.environ, PYTHONPATH="")).wait()

            # Make sure to not install into the default site-packages path, as this would overwrite already pre-installed packages
            if not os.path.exists(packages_path):
                os.mkdir(packages_path)

            # Collect already installed packages by calling pip list (outputs: <package name>==<version>)
            installed_packages = subprocess.check_output([python_bin, "-m", "pip", "list", "--format=freeze", "--path={}".format(pre_python_package_path)])
            installed_packages += subprocess.check_output([python_bin, "-m", "pip", "list", "--format=freeze", "--path={}".format(packages_path)])

            # Split up strings into two lists (names and versions)
            installed_packages_name, installed_packages_versions = zip(*[str(line).lower().split('==') for line in installed_packages.splitlines()])
            installed_packages_name = [ele[2:] if ele.startswith("b'") else ele for ele in installed_packages_name]
            installed_packages_versions = [ele[:-1] if ele.endswith("'") else ele for ele in installed_packages_versions]
            SetupUtility.installed_packages = dict(zip(installed_packages_name, installed_packages_versions))

    @staticmethod
    def extract_file(output_dir, file, mode="ZIP"):
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
                raise Exception("No such mode: " + mode)

        except (IOError, zipfile.BadZipfile) as e:
            print('Bad zip file given as input.  %s' % e)
            raise e

    @staticmethod
    def extract_from_response(output_dir, response):
        """ Extract all members from the archive to output_dir

        :param output_dir: the dir to zip file extract to
        :param response: the response to a requested url that contains a zip file
        """
        file = BytesIO(response.content)
        SetupUtility.extract_file(output_dir, file)

    @staticmethod
    def check_if_setup_utilities_are_at_the_top(path_to_run_file):
        """
        Checks if the given python scripts has at the top an import to SetupUtility, if not an
        exception is thrown. With an explanation that each python script has to start with SetupUtility.

        :param path_to_run_file: path to the used python script
        """
        if os.path.exists(path_to_run_file):
            with open(path_to_run_file, "r") as file:
                text = file.read()
                lines = [l.strip() for l in text.split("\n")]
                lines = [l for l in lines if l and not l.startswith("#")]
                for index, line in enumerate(lines):
                    if "import" in line and "SetupUtility" in line:
                        return
                    elif "import" in line:
                        code = "\n".join(lines[:index + 2])
                        raise Exception('The given script "{}" does not have a SetupUtility call at the top! '
                                        "Make sure that is the first thing you import and run! Before importing "
                                        "anything else!\nYour code:\n#####################\n{}\n"
                                        "####################\nReplaces this with:\nfrom src.utility.SetupUtility "
                                        "import SetupUtility\nSetupUtility.setup([])".format(path_to_run_file, code))
        else:
            raise Exception("The given run script does not exist: {}".format(path_to_run_file))


