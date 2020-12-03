# blender --background --python run.py  -- <config> [<args>]
import sys
import os

# Add path to custom packages inside the blender main directory
sys.path.append(os.path.join(os.path.dirname(sys.executable), "..", "..", "..", "custom-python-packages"))

# this path might need to be changed for you
sphinx_build_bin_path = "/usr/local/bin/sphinx-build"

# Read args
sys.argv = [sphinx_build_bin_path] + sys.argv[sys.argv.index("--") + 1:]

print(sys.argv, os.getcwd())

exec(open(sphinx_build_bin_path).read())