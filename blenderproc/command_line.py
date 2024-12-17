""" Command line function definition. """

import argparse
import os
import signal
import sys
import shutil
import subprocess

repo_root_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(repo_root_directory)

# pylint: disable=wrong-import-position
from blenderproc.python.utility.SetupUtility import SetupUtility, is_using_external_bpy_module
from blenderproc.python.utility.InstallUtility import InstallUtility
# pylint: enable=wrong-import-position


def cli():
    """
    Command line function, parses the arguments given to BlenderProc.
    """
    options = {
        "vis": {
            'hdf5': "Visualizes the content of one or multiple .hdf5 files.",
            'coco': "Visualizes the annotations written in coco format."
        },
        "extract": {
            'hdf5': "Extracts images out of an hdf5 file into separate image files."
        },
        "download": {
            'blenderkit': "Downloads materials and models from blenderkit.",
            'cc_textures': "Downloads textures from cc0textures.com.",
            'haven': "Downloads HDRIs, Textures and Models from polyhaven.com.",
            'ikea': "Downloads the IKEA dataset.",
            'pix3d': "Downloads the Pix3D dataset.",
            'scenenet': "Downloads the scenenet dataset.",
            'matterport3d': "Downloads the Matterport3D dataset."
        },
        "pip": {
            'install': "Installs package in the Blender python environment",
            'uninstall': "Uninstalls package in the Blender python environment"
        },
        "quickstart": {
        }
    }

    parser = argparse.ArgumentParser(description="BlenderProc: A procedural Blender pipeline for "
                                                 "photorealistic image generation.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-v', '--version', action='store_true', help='Version of BlenderProc')
    subparsers = parser.add_subparsers(dest='mode', help="Select a BlenderProc command to run:")

    # Setup different modes
    parser_run = subparsers.add_parser('run', help="Runs the BlenderProc pipeline in normal mode.")
    parser_quickstart = subparsers.add_parser('quickstart',
                                              help="Runs a quickstart script blenderproc/scripts/quickstart.py")
    parser_debug = subparsers.add_parser('debug', help="Runs the BlenderProc pipeline in debug mode. This will open "
                                                       "the Blender UI, so the 3D scene created by the pipeline "
                                                       "can be visually inspected.")
    parser_vis = subparsers.add_parser('vis', help=f"Visualize the content of BlenderProc output files. \n"
                                                   f"Options: {', '.join(options['vis'])}",
                                       formatter_class=argparse.RawTextHelpFormatter)
    parser_download = subparsers.add_parser('download', help="Download datasets, materials or 3D models to run "
                                                             "examples or your own pipeline. \n"
                                                             f"Options: {', '.join(options['download'])}",
                                            formatter_class=argparse.RawTextHelpFormatter)
    parser_extract = subparsers.add_parser('extract', help="Extract the raw images from generated containers such "
                                                           f"as hdf5. \nOptions: {', '.join(options['extract'])}",
                                           formatter_class=argparse.RawTextHelpFormatter)
    parser_pip = subparsers.add_parser('pip', help="Can be used to install/uninstall pip packages in the Blender "
                                                   f"python environment. \nOptions: {', '.join(options['pip'])}",
                                       formatter_class=argparse.RawTextHelpFormatter)

    sub_parser_vis = parser_vis.add_subparsers(dest='vis_mode')
    for cmd, help_str in options['vis'].items():
        sub_parser_vis.add_parser(cmd, help=help_str, add_help=False)

    sub_parser_download = parser_download.add_subparsers(dest='download_mode')
    for cmd, help_str in options['download'].items():
        sub_parser_download.add_parser(cmd, help=help_str, add_help=False)

    sub_parser_extract = parser_extract.add_subparsers(dest='extract_mode')
    for cmd, help_str in options['extract'].items():
        sub_parser_extract.add_parser(cmd, help=help_str, add_help=False)

    parser_pip.add_argument('pip_mode', choices=options['pip'],
                            help='\n'.join(f"{key}: {value}" for key, value in options["pip"].items()))
    parser_pip.add_argument('pip_packages', metavar='pip_packages', nargs='*',
                            help='A list of pip packages that should be installed/uninstalled. '
                                 'Packages versions can be determined via the `==` notation.')
    parser_pip.add_argument('--not-use-custom-package-path', dest='not_use_custom_package_path', action='store_true',
                            help='If set, the pip packages will not be installed into the separate custom package '
                                 'folder, but into blenders python site-packages folder. This should only be used, '
                                 'if a specific pip package cannot be installed into a custom package path.')

    # Setup all common arguments of run and debug mode
    for subparser in [parser_run, parser_debug, parser_quickstart]:
        if subparser != parser_quickstart:
            subparser.add_argument('file', help='The path to a python file which uses BlenderProc via the API.')

        subparser.add_argument('--reinstall-blender', dest='reinstall_blender', action='store_true',
                               help='If given, the blender installation is deleted and reinstalled. Is ignored, if '
                                    'a "custom-blender-path" is given.')
        subparser.add_argument('--temp-dir', dest='temp_dir', default=None,
                               help="The path to a directory where all temporary output files should be stored. "
                                    "If it doesn't exist, it is created automatically. Type: string. Default: "
                                    "\"/dev/shm\" or \"/tmp/\" depending on which is available.")
        subparser.add_argument('--keep-temp-dir', dest='keep_temp_dir', action='store_true',
                               help="If set, the temporary directory is not removed in the end.")
        subparser.add_argument('--force-pip-update', dest='force_pip_update', action='store_true',
                               help="If set, the cache of installed pip packages will be ignored and rebuild "
                                    "based on pip freeze.")

    # Setup common arguments of run, debug and pip mode
    for subparser in [parser_run, parser_debug, parser_pip, parser_quickstart]:
        subparser.add_argument('--blender-install-path', dest='blender_install_path', default=None,
                               help="Set path where blender should be installed. If None is given, "
                                    "/home_local/<env:USER>/blender/ is used per default.")
        subparser.add_argument('--custom-blender-path', dest='custom_blender_path', default=None,
                               help="Set, if you want to use a custom blender installation to run BlenderProc. "
                                    "If None is given, blender is installed into the configured blender_install_path. ")

    args, unknown_args = parser.parse_known_args()

    if args.version:
        # pylint: disable=import-outside-toplevel
        from blenderproc import __version__
        # pylint: enable=import-outside-toplevel
        print(__version__)
    elif args.mode in ["run", "debug", "quickstart"]:
        # BlenderProc has two modes based on the environment variable USE_EXTERNAL_BPY_MODULE. If the
        # variable is set, we expect the bpy module and all relevant dependencies to be provided from the outside.
        # If not set, the script will install blender, setup the environment and run the script inside Blender. 

        # Any run commands are not supported in this mode and have to be executed directly via python.
        if is_using_external_bpy_module():
            if args.mode == "run":
                print("USE_EXTERNAL_BPY_MODULE is set, run the script directly through python:\n\n"
                    f"python {args.file}")
            elif args.mode == "debug":
                print("USE_EXTERNAL_BPY_MODULE is set, debug mode is not supported.")
            elif args.mode == "quickstart":
                path_src_run = os.path.join(repo_root_directory, "blenderproc", "scripts", "quickstart.py")
                print(f"USE_EXTERNAL_BPY_MODULE is set, quickstart is not supported, instead run:\n\n"
                      f"python {os.path.join(path_src_run)}")
            
            sys.exit(1)

        # Setup script path that should be executed
        if args.mode == "quickstart":
            path_src_run = os.path.join(repo_root_directory, "blenderproc", "scripts", "quickstart.py")
            args.file = path_src_run
            print(f"'blenderproc quickstart' is an alias for 'blenderproc run {path_src_run}'")
        else:
            path_src_run = args.file
            SetupUtility.check_if_setup_utilities_are_at_the_top(path_src_run)

        # Setup temp dir
        temp_dir = SetupUtility.determine_temp_dir(args.temp_dir)

        # Setup env vars
        used_environment = dict(os.environ, PYTHONPATH=repo_root_directory, PYTHONNOUSERSITE="1")
        # this is done to enable the import of blenderproc inside the blender internal python environment
        used_environment["INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT"] = "1"

        # Install blender, if not already done
        custom_blender_path, blender_install_path = InstallUtility.determine_blender_install_path(args)
        blender_run_path, major_version = InstallUtility.make_sure_blender_is_installed(custom_blender_path,
                                                                                        blender_install_path,
                                                                                        args.reinstall_blender)
        # If pip update is forced, remove pip package cache
        if args.force_pip_update:
            SetupUtility.clean_installed_packages_cache(os.path.dirname(blender_run_path), major_version)

        # Run either in debug or in normal mode
        if args.mode == "debug":
            # pylint: disable=consider-using-with
            p = subprocess.Popen([blender_run_path, "--python-use-system-env", "--python-exit-code", "0", "--python",
                                os.path.join(repo_root_directory, "blenderproc/debug_startup.py"), "--",
                                path_src_run, temp_dir] + unknown_args,
                                env=used_environment)
            # pylint: enable=consider-using-with
        else:
            # pylint: disable=consider-using-with
            p = subprocess.Popen([blender_run_path, "--background", "--python-use-system-env", "--python-exit-code",
                                "2", "--python", path_src_run, "--", args.file, temp_dir] + unknown_args,
                                env=used_environment)
            # pylint: enable=consider-using-with

        def clean_temp_dir():
            # If temp dir should not be kept and temp dir still exists => remove it,
            # in external bpy mode this is handled in the `Initializer`.
            if not args.keep_temp_dir and os.path.exists(temp_dir):
                print("Cleaning temporary directory")
                shutil.rmtree(temp_dir)

        # Listen for SIGTERM signal, so we can properly clean up and terminate the child process
        def handle_sigterm(_signum, _frame):
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

        sys.exit(p.returncode)
    # Import the required entry point
    elif args.mode in ["vis", "extract", "download"]:
        # pylint: disable=import-outside-toplevel
        if args.mode == "vis" and args.vis_mode == "hdf5":
            from blenderproc.scripts.visHdf5Files import cli as current_cli
        elif args.mode == "vis" and args.vis_mode == "coco":
            from blenderproc.scripts.vis_coco_annotation import cli as current_cli
        elif args.mode == "extract" and args.extract_mode == "hdf5":
            from blenderproc.scripts.saveAsImg import cli as current_cli
        elif args.mode == "download" and args.download_mode == "blenderkit":
            from blenderproc.scripts.download_blenderkit import cli as current_cli
        elif args.mode == "download" and args.download_mode == "cc_textures":
            from blenderproc.scripts.download_cc_textures import cli as current_cli
        elif args.mode == "download" and args.download_mode == "haven":
            from blenderproc.scripts.download_haven import cli as current_cli
        elif args.mode == "download" and args.download_mode == "ikea":
            from blenderproc.scripts.download_ikea import cli as current_cli
        elif args.mode == "download" and args.download_mode == "pix3d":
            from blenderproc.scripts.download_pix3d import cli as current_cli
        elif args.mode == "download" and args.download_mode == "scenenet":
            from blenderproc.scripts.download_scenenet import cli as current_cli
        elif args.mode == "download" and args.download_mode == "matterport3d":
            from blenderproc.scripts.download_matterport3d import cli as current_cli
        else:
            raise RuntimeError(f"There is no linked script for the command: {args.mode}. "
                               f"Options are: {options[args.mode]}")
        # pylint: enable=import-outside-toplevel

        # Remove the first argument (it's the script name)
        sys.argv = sys.argv[:1] + unknown_args
        # Call the script
        current_cli()
    elif args.mode == "pip":
        if is_using_external_bpy_module():
            # In external mode we can't determine the blender_install_path correctly. Populate with
            # stub values, so the SetupUtility can print the user suggestion in one place.
            blender_path = None
            major_version = None
        else:
            # Install blender, if not already done
            custom_blender_path, blender_install_path = InstallUtility.determine_blender_install_path(args)
            blender_bin, major_version = InstallUtility.make_sure_blender_is_installed(custom_blender_path,
                                                                                    blender_install_path)
            blender_path = os.path.dirname(blender_bin)

        if args.pip_mode == "install":
            SetupUtility.setup_pip(user_required_packages=args.pip_packages, blender_path=blender_path,
                                   major_version=major_version,
                                   use_custom_package_path=not args.not_use_custom_package_path,
                                   install_default_packages=False)
        elif args.pip_mode == "uninstall":
            SetupUtility.uninstall_pip_packages(args.pip_packages, blender_path=blender_path,
                                                major_version=major_version)
    else:
        # If no command is given, print help
        print(parser.format_help())
        sys.exit(0)


if __name__ == "__main__":
    cli()
