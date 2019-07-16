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

with open(args.config, "r") as f:
    json_text = f.read()
    json_text = re.sub(r'^//.*\n?', '', json_text, flags=re.MULTILINE)
    config = json.loads(json_text)

blender_version = config["setup"]["blender_version"]
blender_path = os.path.join("blender", blender_version)
if not os.path.exists(blender_path):
    major_version = blender_version[len("blender-"):len("blender-") + 4]
    url = "https://download.blender.org/release/Blender" + major_version + "/" + blender_version + ".tar.bz2"

    print("Downloading blender from " + url)
    file_tmp = urllib.urlretrieve(url, filename=None)[0]

    tar = tarfile.open(file_tmp)
    tar.extractall("blender")

print("Using blender in " + blender_path)

p = subprocess.Popen([os.path.join(blender_path, "blender"), "--background", "--python", "src/run.py", "--", args.config] + args.args)
try:
    p.wait()
except KeyboardInterrupt:
    try:
       p.terminate()
    except OSError:
       pass
    p.wait()