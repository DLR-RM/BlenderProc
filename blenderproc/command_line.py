import argparse
import os
import shutil
import signal
import sys
repo_root_directory = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(repo_root_directory)

import subprocess
from blenderproc.python.utility.SetupUtility import SetupUtility
from blenderproc.python.utility.InstallUtility import InstallUtility

parser = argparse.ArgumentParser(description="BlenderProc: A procedural Blender pipeline for photorealistic training image generation.")
subparsers = parser.add_subparsers(dest='mode')

# Setup different modes
parser_run = subparsers.add_parser('run', help="Runs the BlenderProc pipeline in normal mode.")
parser_debug = subparsers.add_parser('debug', help="Runs the BlenderProc pipeline in debug mode. This will open the Blender UI, so the 3D scene created by the pipeline can be visually inspected.")

# Setup all common arguments of run and debug mode
for subparser in [parser_run, parser_debug]:
    subparser.add_argument('file', default=None, nargs='?', help='The path to a configuration file which describes what the pipeline should do or a python file which uses BlenderProc via the API.')
    subparser.add_argument('args', metavar='arguments', nargs='*', help='Additional arguments which are used to replace placeholders inside the configuration. <args:i> is hereby replaced by the i-th argument.')

    subparser.add_argument('--reinstall-blender', dest='reinstall_blender', action='store_true', help='If given, the blender installation is deleted and reinstalled. Is ignored, if a "custom_blender_path" is configured in the configuration file.')
    subparser.add_argument('--temp-dir', dest='temp_dir', default=None, help="The path to a directory where all temporary output files should be stored. If it doesn't exist, it is created automatically. Type: string. Default: \"/dev/shm\" or \"/tmp/\" depending on which is available.")
    subparser.add_argument('--keep-temp-dir', dest='keep_temp_dir', action='store_true', help="If set, the temporary directory is not removed in the end.")
    subparser.add_argument('--blender-install-path', dest='blender_install_path', default=None, help="Set path where blender should be installed. If None is given, /home_local/<env:USER>/blender/ is used per default. This argument is ignored if it is specified in the given YAML config.")
    subparser.add_argument('--custom-blender-path', dest='custom_blender_path', default=None, help="Set, if you want to use a custom blender installation to run BlenderProc. If None is given, blender is installed into the configured blender_install_path. This argument is ignored if it is specified in the given YAML config.")

args = parser.parse_args()

if args.mode in ["run", "debug"]:
    # Make sure a file is given
    if args.file is None:
        print(parser.format_help())
        exit(0)

    # Check whether its a python a script or a yaml config
    is_config = not args.file.endswith(".py")

    # Install blender, if not already done
    custom_blender_path, blender_install_path = InstallUtility.determine_blender_install_path(is_config, args)
    blender_run_path = InstallUtility.make_sure_blender_is_installed(custom_blender_path, blender_install_path, args.reinstall_blender)

    # Setup script path that should be executed
    if is_config:
        path_src_run = os.path.join(repo_root_directory, "blenderproc/run.py")
    else:
        path_src_run = args.file
        SetupUtility.check_if_setup_utilities_are_at_the_top(path_src_run)

    # Setup temp dir
    temp_dir = SetupUtility.determine_temp_dir(args.temp_dir)

    # Setup env vars
    used_environment = dict(os.environ, PYTHONPATH=repo_root_directory, PYTHONNOUSERSITE="1")
    # this is done to enable the import of blenderproc inside of the blender internal python environment
    used_environment["INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT"] = "1"

    # Run either in debug or in normal mode
    if args.mode == "debug":
        p = subprocess.Popen([blender_run_path, "--python-use-system-env", "--python-exit-code", "0", "--python", os.path.join(repo_root_directory, "blenderproc/debug_startup.py"), "--", path_src_run if not is_config else args.file, temp_dir] + args.args, env=used_environment)
    else:
        p = subprocess.Popen([blender_run_path, "--background", "--python-use-system-env", "--python-exit-code", "2", "--python", path_src_run, "--", args.file, temp_dir] + args.args, env=used_environment)

    def clean_temp_dir():
        # If temp dir should not be kept and temp dir still exists => remove it
        if not args.keep_temp_dir and os.path.exists(temp_dir):
            print("Cleaning temporary directory")
            shutil.rmtree(temp_dir)

    # Listen for SIGTERM signal, so we can properly cleanup and and terminate the child process
    def handle_sigterm(signum, frame):
        clean_temp_dir()
        p.terminate()

    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        p.wait()
    except KeyboardInterrupt:
        try:
            p.terminate()
        except OSError:
            pass
        p.wait()

    # Clean up
    clean_temp_dir()

    exit(p.returncode)