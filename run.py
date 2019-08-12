import json
import argparse
import os
import urllib
import tarfile
import subprocess

from src.utility.Config import Config

parser = argparse.ArgumentParser()
parser.add_argument('config')
parser.add_argument('args', metavar='N', nargs='*')
parser.add_argument('--reinstall-packages', dest='reinstall_packages', action='store_true')
args = parser.parse_args()

config = Config.read_config_dict(args.config, args.args)
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



# Install required packages
if "pip" in setup_config:
    # Install pip    
    subprocess.Popen(["./python3.7m", "-m", "ensurepip"], cwd=os.path.join(blender_path, major_version, "python", "bin")).wait()
    
    # Make sure to not install into the default site-packages path, as this would overwrite already pre-installed packages
    packages_path = os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
    if not os.path.exists(packages_path):
        os.mkdir(packages_path)

    # Collect already installed packages by calling pip list (outputs: <package name>==<version>)
    installed_packages = subprocess.check_output(["./python3.7m", "-m", "pip", "list", "--format=freeze"], env=dict(os.environ, PYTHONPATH=packages_path), cwd=os.path.join(blender_path, major_version, "python", "bin"))
    installed_packages = [line.split('==')[0] for line in installed_packages.splitlines()]

    # Install all packages
    for package in setup_config["pip"]:
        # Only install if its not already installed (pip would check this itself, but at first downloads the requested package which of course always takes a while)
        if package not in installed_packages or args.reinstall_packages:
            subprocess.Popen(["./python3.7m", "-m", "pip", "install", package, "--target", packages_path, "--upgrade"], cwd=os.path.join(blender_path, major_version, "python", "bin")).wait()

# Run script
p = subprocess.Popen([os.path.join(blender_path, "blender"), "--background", "--python", "src/run.py", "--", args.config] + args.args)
try:
    p.wait()
except KeyboardInterrupt:
    try:
       p.terminate()
    except OSError:
       pass
    p.wait()