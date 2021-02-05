import argparse
import os
from os.path import join
import tarfile
import zipfile
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
from src.utility.ConfigParser import ConfigParser

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('config', default=None, nargs='?', help='The path to the configuration file which describes what the pipeline should do.')
parser.add_argument('args', metavar='arguments', nargs='*', help='Additional arguments which are used to replace placeholders inside the configuration. <args:i> is hereby replaced by the i-th argument.')
parser.add_argument('--reinstall-packages', dest='reinstall_packages', action='store_true', help='If given, all python packages configured inside the configuration file will be reinstalled.')
parser.add_argument('--reinstall-blender', dest='reinstall_blender', action='store_true', help='If given, the blender installation is deleted and reinstalled. Is ignored, if a "custom_blender_path" is configured in the configuration file.')
parser.add_argument('--batch_process', help='Renders a batch of house-cam combinations, by reading a file containing the combinations on each line, where each line is the standard placeholder arguments for rendering a single scene separated by spaces. The value of this option is the path to the index file, no need to add placeholder arguments.')
parser.add_argument('--temp-dir', dest='temp_dir', default=None, help="The path to a directory where all temporary output files should be stored. If it doesn't exist, it is created automatically. Type: string. Default: \"/dev/shm\" or \"/tmp/\" depending on which is available.")
parser.add_argument('--keep-temp-dir', dest='keep_temp_dir', action='store_true', help="If set, the temporary directory is not removed in the end.")
parser.add_argument('-h', '--help', dest='help', action='store_true', help='Show this help message and exit.')
args = parser.parse_args()

if args.config is None:
    print(parser.format_help())
    exit(0)

config_parser = ConfigParser()
config = config_parser.parse(args.config, args.args, args.help, skip_arg_placeholders=(args.batch_process != None)) # Don't parse placeholder args in batch mode.
setup_config = config["setup"]

# If blender should be downloaded automatically
if "custom_blender_path" not in setup_config:
    # Determine path where blender should be installed
    if "blender_install_path" in setup_config:
        blender_install_path = os.path.expanduser(setup_config["blender_install_path"])
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
    # right new only support blender-2.91
    major_version = "2.91"
    minor_version = "0"
    blender_version = "blender-{}.{}".format(major_version, minor_version)
    if platform == "linux" or platform == "linux2":
        blender_version += "-linux64"
        blender_path = os.path.join(blender_install_path, blender_version)
    elif platform == "darwin":
        blender_version += "-macOS"
        blender_path = os.path.join(blender_install_path, "Blender.app")
    elif platform == "win32":
        blender_version += "-windows64"
        blender_path = os.path.join(blender_install_path, blender_version)
    else:
        raise Exception("This system is not supported yet: {}".format(platform))

    # If forced reinstall is demanded, remove existing files
    if os.path.exists(blender_path) and args.reinstall_blender:
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
        if platform == "linux" or platform == "linux2":
            url = "https://download.blender.org/release/Blender" + major_version + "/" + blender_version + ".tar.xz"
        elif platform == "darwin":
            url = "https://download.blender.org/release/Blender" + major_version + "/" + blender_version + ".dmg"
        elif platform == "win32":
            url = "https://download.blender.org/release/Blender" + major_version + "/" + blender_version + ".zip"
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
                with tarfile.open(file_tmp) as tar:
                    tar.extractall(blender_install_path)
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
            with zipfile.ZipFile(file_tmp) as z:
                z.extractall(blender_install_path)
else:
    blender_path = os.path.expanduser(setup_config["custom_blender_path"])

    # Try to get major version of given blender installation
    major_version = None
    for sub_dir in os.listdir(blender_path):
        # Search for the subdirectory which has the major version as its name (e.q. 2.79)
        if os.path.isdir(os.path.join(blender_path, sub_dir)) and sub_dir.replace(".", "").isdigit():
            major_version = sub_dir
            break

    if major_version is None:
        raise Exception("Could not determine major blender version")

print("Using blender in " + blender_path)


general_required_packages = ["pyyaml==5.1.2", "imageio"]

required_packages = general_required_packages
if "pip" in setup_config:
    required_packages += setup_config["pip"]

# Install required packages
if len(required_packages) > 0:
    # Install pip
    if platform == "linux" or platform == "linux2":
        python_bin_folder = os.path.join(blender_path, major_version, "python", "bin")
        python_bin = os.path.join(python_bin_folder, "python3.7m")
        packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
        pre_python_package_path = os.path.join(blender_path, major_version, "python", "lib", "python3.7", "site-packages")
    elif platform == "darwin":
        python_bin_folder = os.path.join(blender_path, "Contents", "Resources", major_version, "python", "bin")
        python_bin = os.path.join(python_bin_folder, "python3.7m")
        packages_path = os.path.abspath(os.path.join(
            blender_path, "Contents", "Resources", "custom-python-packages"))
        pre_python_package_path = os.path.join(blender_path, "Contents", "Resources", major_version, "python", "lib", "python3.7", "site-packages")
    elif platform == "win32":
        python_bin_folder = os.path.join(blender_path, major_version, "python", "bin")
        python_bin = os.path.join(python_bin_folder, "python")
        packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
        pre_python_package_path = os.path.join(blender_path, major_version, "python", "lib", "site-packages")
    else:
        raise Exception("This system is not supported yet: {}".format(platform))
    subprocess.Popen([python_bin, "-m", "ensurepip"], env=dict(os.environ, PYTHONPATH="")).wait()
    # Make sure pip is up-to-date
    subprocess.Popen([python_bin, "-m", "pip", "install", "--upgrade", "pip"], env=dict(os.environ, PYTHONPATH="")).wait()

    # Make sure to not install into the default site-packages path, as this would overwrite already pre-installed packages
    if not os.path.exists(packages_path):
        os.mkdir(packages_path)
    used_env = dict(os.environ, PYTHONPATH=packages_path + ":" + pre_python_package_path)
    # Collect already installed packages by calling pip list (outputs: <package name>==<version>)
    installed_packages = subprocess.check_output([python_bin, "-m", "pip", "list", "--format=freeze",
                                                "--path={}".format(pre_python_package_path)])
    installed_packages += subprocess.check_output([python_bin, "-m", "pip", "list", "--format=freeze",
                                               "--path={}".format(packages_path)])

    # Split up strings into two lists (names and versions)
    installed_packages_name, installed_packages_versions = zip(*[str(line).lower().split('==') for line in installed_packages.splitlines()])
    installed_packages_name = [ele[2:] if ele.startswith("b'") else ele for ele in installed_packages_name]
    installed_packages_versions = [ele[:-1] if ele.endswith("'") else ele for ele in installed_packages_versions]

    # Install all packages
    for package in required_packages:
        # Extract name and target version
        if "==" in package:
            package_name, package_version = package.lower().split('==')
        else:
            package_name, package_version = package.lower(), None

        # If the package is given via git, extract package name from url
        if package_name.startswith("git+"):
            # Extract part after last slash
            package_name = package_name[package_name.rfind("/") + 1:]
            # Replace underscores with dashes as its done by pip
            package_name = package_name.replace("_", "-")

        # Check if package is installed
        already_installed = package_name in installed_packages_name

        # If version check is necessary
        if package_version is not None and already_installed:
            # Check if the correct version is installed
            already_installed = (package_version == installed_packages_versions[installed_packages_name.index(package_name)])
            print("{}:{} was installed: {}".format(package_name, package_version, already_installed))

            # If there is already a different version installed
            if not already_installed:
                # Remove the old version (We have to do this manually, as we are using --target with pip install. There old version are not removed)
                subprocess.Popen([python_bin, "-m", "pip", "uninstall", package_name, "-y"],
                                 env=dict(os.environ, PYTHONPATH=packages_path)).wait()

        # Only install if its not already installed (pip would check this itself, but at first downloads the requested package which of course always takes a while)
        if not already_installed or args.reinstall_packages:
            subprocess.Popen([python_bin, "-m", "pip", "install", package, "--target", packages_path,
                              "--upgrade"], env=dict(os.environ, PYTHONPATH=packages_path)).wait()

# Run script
if platform == "linux" or platform == "linux2":
    blender_run_path = os.path.join(blender_path, "blender")
elif platform == "darwin":
    blender_run_path = os.path.join(blender_path, "Contents", "MacOS", "Blender")
elif platform == "win32":
    blender_run_path = os.path.join(blender_path, "blender")
else:
    raise Exception("This system is not supported yet: {}".format(platform))

repo_root_directory = os.path.dirname(os.path.realpath(__file__))
path_src_run = os.path.join(repo_root_directory, "src/run.py")

# Determine perfect temp dir
if args.temp_dir is None:
    if sys.platform != "win32":
        if os.path.exists("/dev/shm"):
            temp_dir = "/dev/shm"
        else:
            temp_dir = "/tmp"
    else:
        temp_dir = os.getenv("TEMP")
else:
    temp_dir = args.temp_dir
# Generate unique directory name in temp dir
temp_dir = os.path.join(temp_dir, "blender_proc_" + str(uuid.uuid4().hex))
# Create the temp dir
print("Using temporary directory: " + temp_dir)
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)


if not args.batch_process:
    p = subprocess.Popen([blender_run_path, "--background", "--python-exit-code", "2", "--python", path_src_run, "--", args.config, temp_dir] + args.args,
                         env=dict(os.environ, PYTHONPATH=""), cwd=repo_root_directory)
else:  # Pass the index file path containing placeholder args for all input combinations (cam, house, output path)
    p = subprocess.Popen([blender_run_path, "--background", "--python-exit-code", "2", "--python", path_src_run, "--",  args.config, temp_dir, "--batch-process", args.batch_process],
                         env=dict(os.environ, PYTHONPATH=""), cwd=repo_root_directory)


def clean_temp_dir():
    # If temp dir should not be kept and temp dir still exists => remove it
    if not args.keep_temp_dir and os.path.exists(temp_dir):
        print("Cleaning temporary directory")
        shutil.rmtree(temp_dir)

# Listen for SIGTERM signal, so we can properly cleanup and and terminate the child process
def handle_sigterm(signum, frame):
    clean_temp_dir()
    p.terminate()
signal.signal(signal.SIGTERM, handle_sigterm)

try:
    p.wait()
except KeyboardInterrupt:
    try:
        p.terminate()
    except OSError:
        pass
    p.wait()

# Clean up
clean_temp_dir()

exit(p.returncode)
