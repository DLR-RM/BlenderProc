import json
import argparse
import os
import urllib
import tarfile
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('config')
parser.add_argument('args', metavar='N', nargs='*')
args = parser.parse_args()

# Load config
with open(args.config, "r") as f:
    json_text = f.read()
    json_text = re.sub(r'^//.*\n?', '', json_text, flags=re.MULTILINE)
    config = json.loads(json_text)
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
    subprocess.Popen(["./python3.5m", "-m", "ensurepip"], cwd=os.path.join(blender_path, major_version, "python", "bin")).wait()
    
    # Make sure to not install into the default site-packages path, as this would overwrite already pre-installed packages
    packages_path =  os.path.abspath(os.path.join(blender_path, "custom-python-packages"))
    if not os.path.exists(packages_path):
        os.mkdir(packages_path)

    # Install all packages
    for package in setup_config["pip"]:
        subprocess.Popen(["./python3.5m", "-m", "pip", "install", package, "--target", packages_path], cwd=os.path.join(blender_path, major_version, "python", "bin")).wait()

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