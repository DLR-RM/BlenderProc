import argparse
import os
import urllib
import tarfile
import subprocess
import shutil

from src.utility.ConfigParser import ConfigParser

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('config', default=None, nargs='?', help='The path to the configuration file which describes what the pipeline should do.')
parser.add_argument('args', metavar='arguments', nargs='*', help='Additional arguments which are used to replace placeholders inside the configuration. <args:i> is hereby replaced by the i-th argument.')
parser.add_argument('--reinstall-packages', dest='reinstall_packages', action='store_true', help='If given, all python packages configured inside the configuration file will be reinstalled.')
parser.add_argument('--reinstall-blender', dest='reinstall_blender', action='store_true', help='If given, the blender installation is deleted and reinstalled. Is ignored, if a "custom_blender_path" is configured in the configuration file.')
parser.add_argument('--batch_process',help='Renders a batch of house-cam combinations, by reading a file containing the combinations on each line, where each line is the standard placeholder arguments for rendering a single scene separated by spaces. The value of this option is the path to the index file, no need to add placeholder arguments.')
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
        blender_install_path = setup_config["blender_install_path"]
    else:
        blender_install_path = "blender"
        
    # Determine configured version    
    blender_version = setup_config["blender_version"]
    blender_path = os.path.join(blender_install_path, blender_version)
    major_version = blender_version[len("blender-"):len("blender-") + 4]

    # If forced reinstall is demanded, remove existing files
    if os.path.exists(blender_path) and args.reinstall_blender:
        print("Removing existing blender installation")
        shutil.rmtree(blender_path)

    # Download blender if it not already exists
    if not os.path.exists(blender_path):
        url = "https://download.blender.org/release/Blender" + major_version + "/" + blender_version + ".tar.bz2"

        print("Downloading blender from " + url)
        file_tmp = urllib.urlretrieve(url, filename=None)[0]

        tar = tarfile.open(file_tmp)
        tar.extractall(blender_install_path)
else:
    blender_path = setup_config["custom_blender_path"]

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


general_required_packages = ["pyyaml"]

required_packages = general_required_packages
if "pip" in setup_config:
    required_packages += setup_config["pip"]

# Install required packages
if len(required_packages) > 0:
    # Install pip    
    subprocess.Popen(["./python3.7m", "-m", "ensurepip"], env=dict(os.environ, PYTHONPATH=""), cwd=os.path.join(blender_path, major_version, "python", "bin")).wait()
    
    # Make sure to not install into the default site-packages path, as this would overwrite already pre-installed packages
    packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
    if not os.path.exists(packages_path):
        os.mkdir(packages_path)

    # Collect already installed packages by calling pip list (outputs: <package name>==<version>)
    installed_packages = subprocess.check_output(["./python3.7m", "-m", "pip", "list", "--format=freeze"], env=dict(os.environ, PYTHONPATH=packages_path), cwd=os.path.join(blender_path, major_version, "python", "bin"))
    installed_packages = [line.split('==')[0] for line in installed_packages.splitlines()]

    # Install all packages
    for package in required_packages:
        # Only install if its not already installed (pip would check this itself, but at first downloads the requested package which of course always takes a while)
        if package not in installed_packages or args.reinstall_packages:
            subprocess.Popen(["./python3.7m", "-m", "pip", "install", package, "--target", packages_path, "--upgrade"], env=dict(os.environ, PYTHONPATH=""), cwd=os.path.join(blender_path, major_version, "python", "bin")).wait()

# Run script
if not args.batch_process:
    p = subprocess.Popen([os.path.join(blender_path, "blender"), "--background", "--python", "src/run.py", "--", args.config] + args.args, env=dict(os.environ, PYTHONPATH=""))
else: # Pass the index file path containing placeholder args for all input combinations (cam, house, output path)
    p = subprocess.Popen([os.path.join(blender_path, "blender"), "--background", "--python", "src/run.py", "--",  args.config, "--batch-process", args.batch_process], env=dict(os.environ, PYTHONPATH=""))    
try:
    p.wait()
except KeyboardInterrupt:
    try:
       p.terminate()
    except OSError:
       pass
    p.wait()