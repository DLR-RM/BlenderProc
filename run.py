# blender --background --python run.py  -- <config> [<args>]
import os
import bpy
import sys

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import sys
from src.main.Pipeline import Pipeline

started_from_commandline = '--' in sys.argv

if started_from_commandline:
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]
    config_path = argv[0]

    pipeline = Pipeline(config_path, argv[1:])
    pipeline.run()
