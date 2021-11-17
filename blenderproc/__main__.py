import os
os.environ.setdefault("OUTSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT_BUT_IN_RUN_SCRIPT", "1")
from blenderproc.command_line import cli

cli()
