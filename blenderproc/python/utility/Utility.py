import os
import csv
import threading
from typing import List, Dict, Any, Tuple, Optional, Union

import bpy
import time
import inspect
import importlib
import warnings
import numpy as np
import json
from sys import platform
if platform != "win32":
    # importing git doesn't work under windows
    import git

from blenderproc.python.modules.main.GlobalStorage import GlobalStorage
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.types.StructUtilityFunctions import get_instances
from blenderproc.version import __version__


def resolve_path(path: str) -> str:
    """ Returns an absolute path. If given path is relative, current working directory is put in front.

    :param path: The path to resolve.
    :return: The absolute path.
    """
    path = path.strip()

    if path.startswith("/"):
        return path
    elif path.startswith("~"):
        return path.replace("~", os.getenv("HOME"))
    else:
        return os.path.join(os.getcwd(), path)

def resolve_resource(relative_resource_path: str) -> str:
    """ Returns an absolute path to the given BlenderProc resource.

    :param relative_resource_path: The relative path inside the BlenderProc resource folder.
    :return: The absolute path.
    """
    return resolve_path(os.path.join(Utility.blenderproc_root, "blenderproc", "resources", relative_resource_path))

def num_frames() -> int:
    """ Returns the currently total number of registered frames.

    :return: The number of frames.
    """
    return bpy.context.scene.frame_end - bpy.context.scene.frame_start

def reset_keyframes() -> None:
    """ Removes registered keyframes from all objects and resets frame_start and frame_end """
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 0
    for a in bpy.data.actions:
        bpy.data.actions.remove(a)

def set_keyframe_render_interval(frame_start: Optional[int] = None, frame_end: Optional[int] = None):
    """ Sets frame_start and/or frame_end which determine the frames that will be rendered.

    :param frame_start: The new frame_start value. If None, it will be ignored.
    :param frame_end: The new frame_end value. If None, it will be ignored.
    """
    if frame_start is not None:
        bpy.context.scene.frame_start = frame_start
    if frame_end is not None:
        bpy.context.scene.frame_end = frame_end

class Utility:
    blenderproc_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    temp_dir = ""
    used_temp_id = None

    @staticmethod
    def initialize_modules(module_configs: List[Union[Dict[str, Any], str]]) -> List["Module"]:
        """ Initializes the modules described in the given configuration.

        Example for module_configs:


        .. code-block:: yaml

            [{
              "module": "base.ModuleA",
              "config": {...}
            }, ...]

        If you want to execute a certain module several times, add the `amount_of_repetions` on the same level as the
        module name:

        .. code-block:: yaml

            [{
              "module": "base.ModuleA",
              "config": {...},
              "amount_of_repetitions": 3
            }, ...]

        Here the name contains the path to the module class, starting from inside the src directory.

        Be aware that all attributes stored in the GlobalStorage are also accessible here, even though
        they are not copied into the new config.

        :param module_configs: A list of dicts, each one describing one module.
        :return: a list of initialized modules
        """
        modules = []

        for module_config in module_configs:
            # If only the module name is given (short notation)
            if isinstance(module_config, str):
                module_config = {"module": module_config}

            # Initialize config with empty config
            config = {}
            # Check if there is a module specific config
            if "config" in module_config:
                # Overwrite with module specific config
                Utility.merge_dicts(module_config["config"], config)

            # Check if the module has a repetition counter
            amount_of_repetitions = 1
            if "amount_of_repetitions" in module_config:
                amount_of_repetitions = Config(module_config).get_int("amount_of_repetitions")

            with Utility.BlockStopWatch("Initializing module " + module_config["module"]):
                for i in range(amount_of_repetitions):
                    module_class = None
                    # For backwards compatibility we allow to specify a modules also without "Module" suffix.
                    for suffix in ["Module", ""]:
                        try:
                            # Try to load the module using the current suffix
                            module = importlib.import_module(
                                "blenderproc.python.modules." + module_config["module"] + suffix)
                        except ModuleNotFoundError:
                            # Try next suffix
                            continue

                        # Check if the loaded module has a class with the same name
                        class_name = module_config["module"].split(".")[-1] + suffix
                        if hasattr(module, class_name):
                            # Import file and extract class
                            module_class = getattr(module, class_name)
                            break

                    # Throw an error if no module/class with the specified name + any suffix has been found
                    if module_class is None:
                        raise Exception(
                            "The module blenderproc.python.modules." + module_config["module"] + " was not found!")

                    # Create module
                    modules.append(module_class(Config(config)))

        return modules

    @staticmethod
    def get_current_version() -> Optional[str]:
        """ Gets the git commit hash.

        :return: a string, the BlenderProc version, or None if unavailable
        """
        if platform == "win32":
            return __version__
        try:
            repo = git.Repo(search_parent_directories=True)
        except git.InvalidGitRepositoryError as e:
            return __version__
        return repo.head.object.hexsha

    @staticmethod
    def get_temporary_directory() -> str:
        """
        :return: default temporary directory, shared memory if it exists
        """
        return Utility.temp_dir

    @staticmethod
    def merge_dicts(source: Dict[Any, Any], destination: Dict[Any, Any]) -> Dict[Any, Any]:
        """ Recursively copies all key value pairs from src to dest (Overwrites existing)

        :param source: The source dict.
        :param destination: The destination dict
        :return: The modified destination dict.
        """
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                Utility.merge_dicts(value, node)
            else:
                destination[key] = value

        return destination

    @staticmethod
    def hex_to_rgba(hex_value: str) -> List[float]:
        """ Converts the given hex string to rgba color values.

        :param hex_value: The hex string, describing rgb.
        :return: The rgba color, in form of a list. Values between 0 and 1.
        """
        return [x / 255 for x in bytes.fromhex(hex_value[-6:])] + [1.0]

    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """ Converts the given rgb to hex values.

        :param rgb: tuple of three with rgb integers.
        :return: Hex string.
        """
        return '#%02x%02x%02x' % tuple(rgb)

    @staticmethod
    def insert_node_instead_existing_link(links: bpy.types.NodeLinks, source_socket: bpy.types.NodeSocket,
                                          new_node_dest_socket: bpy.types.NodeSocket,
                                          new_node_src_socket: bpy.types.NodeSocket, dest_socket: bpy.types.NodeSocket):
        """ Replaces the node between source_socket and dest_socket with a new node.

        Before: source_socket -> dest_socket
        After: source_socket -> new_node_dest_socket and new_node_src_socket -> dest_socket

        :param links: The collection of all links.
        :param source_socket: The source socket.
        :param new_node_dest_socket: The new destination for the link starting from source_socket.
        :param new_node_src_socket: The new source for the link towards dest_socket.
        :param dest_socket: The destination socket
        """
        for l in links:
            if l.from_socket == source_socket or l.to_socket == dest_socket:
                links.remove(l)

        links.new(source_socket, new_node_dest_socket)
        links.new(new_node_src_socket, dest_socket)

    @staticmethod
    def get_node_connected_to_the_output_and_unlink_it(material: bpy.types.Material) \
            -> Tuple[Optional[bpy.types.Node], bpy.types.Node]:
        """
        Searches for the OutputMaterial in the given material and finds the connected node to it,
        removes the connection between this node and the output and returns this node and the material_output

        :param material: Material on which this operation should be performed
        """
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        material_output = Utility.get_the_one_node_with_type(nodes, 'OutputMaterial')
        # find the node, which is connected to the output
        node_connected_to_the_output = None
        for link in links:
            if link.to_node == material_output:
                node_connected_to_the_output = link.from_node
                # remove this link
                links.remove(link)
                break
        return node_connected_to_the_output, material_output

    @staticmethod
    def get_nodes_with_type(nodes: List[bpy.types.Node], node_type: str) -> List[bpy.types.Node]:
        """
        Returns all nodes which are of the given node_type

        :param nodes: list of nodes of the current material
        :param node_type: node types
        :return: list of nodes, which belong to the type
        """
        return [node for node in nodes if node_type in node.bl_idname]

    @staticmethod
    def get_the_one_node_with_type(nodes: List[bpy.types.Node], node_type: str) -> bpy.types.Node:
        """
        Returns the one nodes which is of the given node_type

        This function will only work if there is only one of the nodes of this type.

        :param nodes: list of nodes of the current material
        :param node_type: node types
        :return: node of the node type
        """
        node = Utility.get_nodes_with_type(nodes, node_type)
        if node and len(node) == 1:
            return node[0]
        else:
            raise Exception("There is not only one node of this type: {}, there are: {}".format(node_type, len(node)))

    @staticmethod
    def read_suncg_lights_windows_materials() -> Tuple[Dict[str, Tuple[List[str], List[str]]], List[str]]:
        """
        Returns the lights dictionary and windows list which contains their respective materials

        :return: dictionary of lights' and list of windows' materials
        """
        # Read in lights
        lights: Dict[str, Tuple[List[str], List[str]]] = {}
        # File format: <obj id> <number of lightbulb materials> <lightbulb material names> <number of lampshade materials> <lampshade material names>
        with open(resolve_resource(os.path.join("suncg", "light_geometry_compact.txt"))) as f:
            lines = f.readlines()
            for row in lines:
                row = row.strip().split()
                lights[row[0]] = ([], [])

                index = 1

                # Read in lightbulb materials
                number = int(row[index])
                index += 1
                for i in range(number):
                    lights[row[0]][0].append(row[index])
                    index += 1

                # Read in lampshade materials
                number = int(row[index])
                index += 1
                for i in range(number):
                    lights[row[0]][1].append(row[index])
                    index += 1

        # Read in windows
        windows = []
        with open(resolve_resource(os.path.join('suncg', 'ModelCategoryMapping.csv')), 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["coarse_grained_class"] == "window":
                    windows.append(row["model_id"])

        return lights, windows

    class BlockStopWatch:
        """ Calls a print statement to mark the start and end of this block and also measures execution time.

        Usage: with BlockStopWatch('text'):
        """

        def __init__(self, block_name):
            self.block_name = block_name

        def __enter__(self):
            print("#### Start - " + self.block_name + " ####")
            self.start = time.time()

        def __exit__(self, type, value, traceback):
            print("#### Finished - " + self.block_name + " (took " + (
                        "%.3f" % (time.time() - self.start)) + " seconds) ####")

    class UndoAfterExecution:
        """ Reverts all changes done to the blender project inside this block.

        Usage: with UndoAfterExecution():
        """

        def __init__(self, check_point_name: Optional[str] = None, perform_undo_op: bool = True):
            if check_point_name is None:
                check_point_name = inspect.stack()[1].filename + " - " + inspect.stack()[1].function
            self.check_point_name = check_point_name
            self._perform_undo_op = perform_undo_op

        def __enter__(self):
            if self._perform_undo_op:
                from blenderproc.python.types.StructUtility import Struct
                # Collect all existing struct instances
                self.struct_instances = get_instances()
                bpy.ops.ed.undo_push(message="before " + self.check_point_name)

        def __exit__(self, type, value, traceback):
            if self._perform_undo_op:
                bpy.ops.ed.undo_push(message="after " + self.check_point_name)
                # The current state points to "after", now by calling undo we go back to "before"
                bpy.ops.ed.undo()
                # After applying undo, all references to blender objects are invalid.
                # Therefore we now go over all instances and update their references using their name as unique identifier.
                for name, struct in self.struct_instances:
                    struct.update_blender_ref(name)

    @staticmethod
    def build_provider(name: str, parameters: Dict[str, Any]) -> "Provider":
        """ Builds up providers like sampler or getter.

        It first builds the config and then constructs the required provider.

        :param name: The name of the provider class.
        :param parameters: A dict containing the parameters that should be used.
        :return: The constructed provider.
        """
        module_class = None
        for suffix in ["Module", ""]:
            try:
                # Import class from blenderproc.python.modules
                module_class = getattr(importlib.import_module("blenderproc.python.modules.provider." + name + suffix),
                                       name.split(".")[-1] + suffix)
                break
            except ModuleNotFoundError:
                # Try next suffix
                continue

        # Throw an error if no module/class with the specified name + any suffix has been found
        if module_class is None:
            raise Exception("The module blenderproc.python.modules.provider." + name + " was not found!")

        # Build configuration
        config = Config(parameters)
        # Construct provider
        return module_class(config)

    @staticmethod
    def build_provider_based_on_config(config: Config) -> "Provider":
        """ Builds up the provider using the parameters described in the given config.

        The given config should follow the following scheme:

        .. code-block:: yaml

            {
              "provider": "<name of provider class>"
              "parameters": {
                <provider parameters>
              }
            }

        :param config: A Configuration object or a dict containing the configuration data.
        :return: The constructed provider.
        """
        if isinstance(config, dict):
            config = Config(config)

        parameters = {}
        for key in config.data.keys():
            if key != 'provider':
                parameters[key] = config.data[key]

        if not config.has_param('provider'):
            raise Exception(
                "Each provider needs a provider label, this one does not contain one: {}".format(config.data))

        return Utility.build_provider(config.get_string("provider"), parameters)

    @staticmethod
    def generate_equidistant_values(num: int, space_size_per_dimension: int) -> Tuple[List[List[int]], int]:
        """ This function generates N equidistant values in a 3-dim space and returns num of them.

        Every dimension of the space is limited by [0, K], where K is the given space_size_per_dimension.
        Basically it splits a cube of shape K x K x K in to N smaller blocks. Where, N = cube_length^3
        and cube_length is the smallest integer for which N >= num.

        If K is not a multiple of N, then the sum of all blocks might
        not fill up the whole K ** 3 cube.

        :param num: The total number of values required.
        :param space_size_per_dimension: The side length of cube.
        """
        num_splits_per_dimension = 1
        values = []
        # find cube_length bound of cubes to be made
        while num_splits_per_dimension ** 3 < num:
            num_splits_per_dimension += 1

        # Calc the side length of a block. We do a integer division here, s.t. we get blocks with the exact same size,
        # even though we are then not using the full space of [0, 255] ** 3
        block_length = space_size_per_dimension // num_splits_per_dimension

        # Calculate the center of each block and use them as equidistant values
        r_mid_point = block_length // 2
        for r in range(num_splits_per_dimension):
            g_mid_point = block_length // 2
            for g in range(num_splits_per_dimension):
                b_mid_point = block_length // 2
                for b in range(num_splits_per_dimension):
                    values.append([r_mid_point, g_mid_point, b_mid_point])
                    b_mid_point += block_length
                g_mid_point += block_length
            r_mid_point += block_length
        return values[:num], num_splits_per_dimension

    @staticmethod
    def map_back_from_equally_spaced_equidistant_values(values: np.ndarray, num_splits_per_dimension: int,
                                                        space_size_per_dimension: int) -> np.ndarray:
        """ Maps the given values back to their original indices.

        This function calculates for each given value the corresponding index in the list of values created by the generate_equidistant_values() method.

        :param values: An array of shape [M, N, 3];
        :param num_splits_per_dimension: The number of splits per dimension that were made when building up the equidistant values.
        :return: A 2-dim array of indices corresponding to the given values.
        """
        # Calc the side length of a block.
        block_length = space_size_per_dimension // num_splits_per_dimension
        # Subtract a half of a block from all values, s.t. now every value points to the lower corner of a block
        values -= block_length // 2
        # this clipping is necessary to avoid that numbers below zero are than used in an uint16
        values = np.clip(values, 0, space_size_per_dimension)
        # Calculate the block indices per dimension
        values /= block_length
        # Compute the global index of the block (corresponds to the three nested for loops inside generate_equidistant_values())
        values = values[:, :, 0] * num_splits_per_dimension * num_splits_per_dimension + values[:, :,1] * num_splits_per_dimension + values[:, :, 2]
        # Round the values, s.t. derivations are put back to their closest index.
        return np.round(values)

    @staticmethod
    def add_output_entry(output: Dict[str, str]):
        """ Registers the given output in the scene's custom properties

        :param output: A dict containing key and path of the new output type.
        """
        if GlobalStorage.is_in_storage("output"):
            # E.g. multiple camera samplers
            if not Utility.output_already_registered(output, GlobalStorage.get("output")):
                GlobalStorage.get("output").append(output)
        else:
            GlobalStorage.set("output", [output])

    @staticmethod
    def register_output(output_dir: str, prefix: str, key: str, suffix: str, version: str,
                        unique_for_camposes: bool = True):
        """ Registers new output type using configured key and file prefix.

        :param output_dir: The output directory containing the generated files.
        :param prefix: The default prefix of the generated files.
        :param key: The default key which should be used for storing the output in merged file.
        :param suffix: The suffix of the generated files.
        :param version: The version number which will be stored at key_version in the final merged file.
        :param unique_for_camposes: True if the output to be registered is unique for all the camera poses
        """

        Utility.add_output_entry({
            "key": key,
            "path": os.path.join(output_dir, prefix) + ("%04d" if unique_for_camposes else "") + suffix,
            "version": version
        })

    @staticmethod
    def find_registered_output_by_key(key: str) -> Optional[Any]:
        """ Returns the output which was registered with the given key.

        :param key: The output key to look for.
        :return: The dict containing all information registered for that output. If no output with the given key exists, None is returned.
        """
        for output in Utility.get_registered_outputs():
            if output["key"] == key:
                return output

        return None

    @staticmethod
    def get_registered_outputs() -> List[Dict[str, Any]]:
        """ Returns a list of outputs which were registered.

        :return: A list of dicts containing all information registered for the outputs. 
        """
        outputs = []
        if GlobalStorage.is_in_storage("output"):
            outputs = GlobalStorage.get("output")

        return outputs

    @staticmethod
    def output_already_registered(output: Dict[str, Any], output_list: List[Dict[str, Any]]) -> bool:
        """ Checks if the given output entry already exists in the list of outputs, by checking on the key and path.
        Also throws an error if it detects an entry having the same key but not the same path and vice versa since this
        is ambiguous.

        :param output: The output dict entry.
        :param output_list: The list of output entries.
        :return: bool indicating whether it already exists.
        """
        for _output in output_list:
            if output["key"] == _output["key"] and output["path"] == _output["path"]:
                print("Warning! Detected output entries with duplicate keys and paths")
                return True
            if output["key"] == _output["key"] or output["path"] == _output["path"]:
                raise Exception("Can not have two output entries with the same key/path but not same path/key." +
                                "Original entry's data: key:{} path:{}, Entry to be registered: key:{} path:{}"
                                .format(_output["key"], _output["path"], output["key"], output["path"]))

        return False

    @staticmethod
    def insert_keyframe(obj: bpy.types.Object, data_path: str, frame: Optional[int] = None):
        """ Inserts a keyframe for the given object and data path at the specified frame number:

        :param obj: The blender object to use.
        :param data_path: The data path of the attribute.
        :param frame: The frame number to use. If None is given, the current frame number is used.
        """
        # If no frame is given use the current frame specified by the surrounding KeyFrame context manager
        if frame is None and KeyFrame.is_any_active():
            frame = bpy.context.scene.frame_current
        # If no frame is given and no KeyFrame context manager surrounds us => do nothing
        if frame is not None:
            obj.keyframe_insert(data_path=data_path, frame=frame)


# KeyFrameState should be thread-specific
class KeyFrameState(threading.local):
    def __init__(self):
        super(KeyFrameState, self).__init__()
        self.depth = 0


class KeyFrame:
    # Remember how many KeyFrame context manager have been applied around the current execution point
    state = KeyFrameState()

    def __init__(self, frame: int):
        """ Sets the frame number for its complete block.

        :param frame: The frame number to set. If None is given, nothing is changed.
        """
        self._frame = frame
        self._prev_frame = None

    def __enter__(self):
        KeyFrame.state.depth += 1
        if self._frame is not None:
            self._prev_frame = bpy.context.scene.frame_current
            bpy.context.scene.frame_set(self._frame)

    def __exit__(self, type, value, traceback):
        KeyFrame.state.depth -= 1
        if self._prev_frame is not None:
            bpy.context.scene.frame_set(self._prev_frame)

    @staticmethod
    def is_any_active() -> bool:
        """ Returns whether the current execution point is surrounded by a KeyFrame context manager.

        :return: True, if there is at least one surrounding KeyFrame context manager
        """
        return KeyFrame.state.depth > 0


class NumpyEncoder(json.JSONEncoder):
    """ A json encoder that is also capable of serializing numpy arrays """

    def default(self, obj):
        # If its a numpy array
        if isinstance(obj, np.ndarray):
            # Convert it to a list
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
