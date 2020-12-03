# blender --background --python run.py  -- <config> [<args>]
import sys
import os

# Add path to custom packages inside the blender main directory
sys.path.append(os.path.join(os.path.dirname(sys.executable), "..", "..", "..", "custom-python-packages"))

# Read args
sys.argv = ["/usr/local/bin/sphinx-build"] + sys.argv[sys.argv.index("--") + 1:]

print(sys.argv, os.getcwd())

exec(open("/usr/local/bin/sphinx-build").read())