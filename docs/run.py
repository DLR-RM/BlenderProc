# blender --background --python cli.py  -- <config> [<args>]
import sys
import os
from shutil import which

# Add path to custom packages inside the blender main directory
sys.path.append(os.path.join(os.path.dirname(sys.executable), "..", "..", "..", "custom-python-packages"))

# Determine abs path to sphinx-build
sphinx_build_bin_path = which('sphinx-build')

# Read args
sys.argv = [sphinx_build_bin_path] + sys.argv[sys.argv.index("--") + 1:]

print(sys.argv, os.getcwd())

exec(open(sphinx_build_bin_path).read())
