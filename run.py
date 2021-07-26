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
from src.utility.ConfigParser import ConfigParser
from src.utility.SetupUtility import SetupUtility


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('file', default=None, nargs='?', help='The path to a configuration file which describes what the pipeline should do or a python file which uses BlenderProc via the API.')
parser.add_argument('args', metavar='arguments', nargs='*', help='Additional arguments which are used to replace placeholders inside the configuration. <args:i> is hereby replaced by the i-th argument.')
parser.add_argument('--reinstall-blender', dest='reinstall_blender', action='store_true', help='If given, the blender installation is deleted and reinstalled. Is ignored, if a "custom_blender_path" is configured in the configuration file.')
parser.add_argument('--batch_process', help='Renders a batch of house-cam combinations, by reading a file containing the combinations on each line, where each line is the standard placeholder arguments for rendering a single scene separated by spaces. The value of this option is the path to the index file, no need to add placeholder arguments.')
parser.add_argument('--temp-dir', dest='temp_dir', default=None, help="The path to a directory where all temporary output files should be stored. If it doesn't exist, it is created automatically. Type: string. Default: \"/dev/shm\" or \"/tmp/\" depending on which is available.")
parser.add_argument('--keep-temp-dir', dest='keep_temp_dir', action='store_true', help="If set, the temporary directory is not removed in the end.")
parser.add_argument('--blender-install-path', dest='blender_install_path', default=None, help="Set path where blender should be installed. If None is given, /home_local/<env:USER>/blender/ is used per default. This argument is ignored if it is specified in the given YAML config.")
parser.add_argument('--custom-blender-path', dest='custom_blender_path', default=None, help="Set, if you want to use a custom blender installation to run BlenderProc. If None is given, blender is installed into the configured blender_install_path. This argument is ignored if it is specified in the given YAML config.")
parser.add_argument('--debug', action='store_true', help="If True, the Blender UI will open up and everything will be prepared to run BlenderProc inside. This is great for debugging. The given arguments will be also available inside the blender UI.")
parser.add_argument('-h', '--help', dest='help', action='store_true', help='Show this help message and exit.')
args = parser.parse_args()

if args.file is None:
    print(parser.format_help())
    exit(0)

# If a config is given we can extract some information out of it
is_config = not args.file.endswith(".py")
if is_config:
    config_parser = ConfigParser()
    config = config_parser.parse(args.file, args.args, args.help, skip_arg_placeholders=(args.batch_process != None)) # Don't parse placeholder args in batch mode.
    setup_config = config["setup"]
    custom_blender_path = setup_config["custom_blender_path"] if "custom_blender_path" in setup_config else args.custom_blender_path
    blender_install_path = setup_config["blender_install_path"] if "blender_install_path" in setup_config else args.blender_install_path
else:
    custom_blender_path = args.custom_blender_path
    blender_install_path = args.blender_install_path

    # If no blender install path is given set it to /home_local/<env:USER>/blender/ per default
    if blender_install_path is None:
        blender_install_path = os.path.join("/home_local", os.getenv("USERNAME") if platform == "win32" else os.getenv("USER"), "blender")

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
            SetupUtility.extract_file(file_tmp, blender_install_path)
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

repo_root_directory = os.path.dirname(os.path.realpath(__file__))
if is_config:
    path_src_run = os.path.join(repo_root_directory, "src/run.py")
else:
    path_src_run = args.file
    SetupUtility.check_if_setup_utilities_are_at_the_top(path_src_run)

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

if args.debug:
    p = subprocess.Popen([blender_run_path, "--python-use-system-env", "--python-exit-code", "0", "--python", "src/debug_startup.py", "--", path_src_run if not is_config else args.file, temp_dir] + args.args, env=dict(os.environ, PYTHONPATH=os.getcwd(), PYTHONNOUSERSITE="1"), cwd=repo_root_directory)
else:
    if not args.batch_process:
        p = subprocess.Popen([blender_run_path, "--background", "--python-use-system-env", "--python-exit-code", "2", "--python", path_src_run, "--", args.file, temp_dir] + args.args,
                             env=dict(os.environ, PYTHONPATH=os.getcwd(), PYTHONNOUSERSITE="1"), cwd=repo_root_directory)
    else:  # Pass the index file path containing placeholder args for all input combinations (cam, house, output path)
        p = subprocess.Popen([blender_run_path, "--background", "--python-use-system-env", "--python-exit-code", "2", "--python", path_src_run, "--",  args.file, temp_dir, "--batch-process", args.batch_process],
                             env=dict(os.environ, PYTHONPATH=os.getcwd(), PYTHONNOUSERSITE="1"), cwd=repo_root_directory)


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
