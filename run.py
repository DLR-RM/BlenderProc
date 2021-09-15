import argparse
import sys
from blenderproc.command_line import cli

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('file', default=None, nargs='?', help='The path to a configuration file which describes what the pipeline should do or a python file which uses BlenderProc via the API.')
parser.add_argument('args', metavar='arguments', nargs='*', help='Additional arguments which are used to replace placeholders inside the configuration. <args:i> is hereby replaced by the i-th argument.')
parser.add_argument('--reinstall-blender', dest='reinstall_blender', action='store_true', help='If given, the blender installation is deleted and reinstalled. Is ignored, if a "custom_blender_path" is configured in the configuration file.')
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

# Change from old to new CLI format
if args.debug:
    sys.argv.insert(1, "debug")
    sys.argv.remove("--debug")
else:
    sys.argv.insert(1, "run")

# Run the actual CLI, this is just a fallback script
cli()

