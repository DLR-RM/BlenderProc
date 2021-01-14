import os
import math
import uuid
import bpy
import time
import inspect
import importlib

from src.main.GlobalStorage import GlobalStorage
from src.utility.Config import Config
from mathutils import Matrix, Vector
import numpy as np

class Utility:
    working_dir = ""
    temp_dir = ""
    used_temp_id = None

    @staticmethod
    def initialize_modules(module_configs):
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
                amount_of_repetitions = module_config["amount_of_repetitions"]

            with Utility.BlockStopWatch("Initializing module " + module_config["module"]):
                for i in range(amount_of_repetitions):
                    # Import file and extract class
                    module_class = getattr(importlib.import_module("src." + module_config["module"]), module_config["module"].split(".")[-1])
                    # Create module
                    modules.append(module_class(Config(config)))

        return modules


    @staticmethod
    def transform_matrix_to_blender_coord_frame(matrix, source_frame):
        """ Transforms the given homog into the blender coordinate frame.

        :param matrix: The matrix to convert in form of a mathutils.Matrix.
        :param frame_of_point: An array containing three elements, describing the axes of the coordinate frame of the \
                               source frame. (Allowed values: "X", "Y", "Z", "-X", "-Y", "-Z")
        :return: The converted point is in form of a mathutils.Matrix.
        """
        assert len(source_frame) == 3, "The specified coordinate frame has more or less than tree axes: {}".format(frame_of_point)
        output = np.eye(4)
        for i, axis in enumerate(source_frame):
            axis = axis.upper()

            if axis.endswith("X"):
                output[:4,0] = matrix.col[0]
            elif axis.endswith("Y"):
                output[:4,1] = matrix.col[1]
            elif axis.endswith("Z"):
                output[:4,2] = matrix.col[2]
            else:
                raise Exception("Invalid axis: " + axis)

            if axis.startswith("-"):
                output[:3, i] *= -1

        output[:4,3] = matrix.col[3]
        output = Matrix(output)
        return output

    @staticmethod
    def resolve_path(path):
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
            return os.path.join(os.path.dirname(Utility.working_dir), path)

    @staticmethod
    def get_temporary_directory():
        """
        :return: default temporary directory, shared memory if it exists
        """
        return Utility.temp_dir

    @staticmethod
    def merge_dicts(source, destination):
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
    def hex_to_rgba(hex):
        """ Converts the given hex string to rgba color values.

        :param hex: The hex string, describing rgb.
        :return: The rgba color, in form of a list. Values between 0 and 1.
        """
        return [x / 255 for x in bytes.fromhex(hex[-6:])] + [1.0]

    @staticmethod
    def rgb_to_hex(rgb):
        """ Converts the given rgb to hex values.

        :param rgb: tuple of three with rgb integers.
        :return: Hex string.
        """
        return '#%02x%02x%02x' % tuple(rgb)

    @staticmethod
    def get_idx(array,item):
        """
        Returns index of an element if it exists in the list

        :param array: a list with values for which == operator works.
        :param item: item to find the index of
        :return: index of item, -1 otherwise
        """
        try:
            return array.index(item)
        except ValueError:
            return -1

    @staticmethod
    def insert_node_instead_existing_link(links, source_socket, new_node_dest_socket, new_node_src_socket, dest_socket):
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
        links.new(new_node_src_socket, dest_socket)\

    @staticmethod
    def get_node_connected_to_the_output_and_unlink_it(material):
        """
        Searches for the OutputMaterial in the given material and finds the connected node to it,
        removes the connection between this node and the output and returns this node and the material_output

        :param material_slot: material slot
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
    def get_nodes_with_type(nodes, node_type):
        """
        Returns all nodes which are of the given node_type

        :param nodes: list of nodes of the current material
        :param node_type: node types
        :return: list of nodes, which belong to the type
        """
        return [node for node in nodes if node_type in node.bl_idname]

    @staticmethod
    def get_the_one_node_with_type(nodes, node_type):
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
            raise Exception("There is not only one node of this type: {}".format(node_type))

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
            print("#### Finished - " + self.block_name + " (took " + ("%.3f" % (time.time() - self.start)) + " seconds) ####")

    class UndoAfterExecution:
        """ Reverts all changes done to the blender project inside this block.

        Usage: with UndoAfterExecution():
        """
        def __init__(self, check_point_name=None, perform_undo_op=True):
            if check_point_name is None:
                check_point_name = inspect.stack()[1].filename + " - " + inspect.stack()[1].function
            self.check_point_name = check_point_name
            self._perform_undo_op = perform_undo_op

        def __enter__(self):
            if self._perform_undo_op:
                bpy.ops.ed.undo_push(message="before " + self.check_point_name)

        def __exit__(self, type, value, traceback):
            if self._perform_undo_op:
                bpy.ops.ed.undo_push(message="after " + self.check_point_name)
                # The current state points to "after", now by calling undo we go back to "before"
                bpy.ops.ed.undo()

    @staticmethod
    def build_provider(name, parameters):
        """ Builds up providers like sampler or getter.

        It first builds the config and then constructs the required provider.

        :param name: The name of the provider class.
        :param parameters: A dict containing the parameters that should be used.
        :return: The constructed provider.
        """
        # Import class from src.utility
        module_class = getattr(importlib.import_module("src.provider." + name), name.split(".")[-1])
        # Build configuration
        config = Config(parameters)
        # Construct provider
        return module_class(config)

    @staticmethod
    def build_provider_based_on_config(config):
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
            raise Exception("Each provider needs an provider label, this one does not contain one: {}".format(config.data))

        return Utility.build_provider(config.get_string("provider"), parameters)

    @staticmethod
    def generate_equidistant_values(num, space_size_per_dimension):
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

        # Calc the side length of a block. We do a integer division here, s.t. we get blocks with the exact same size, even though we are then not using the full space of [0, 255] ** 3
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
    def map_back_from_equally_spaced_equidistant_values(values, num_splits_per_dimension, space_size_per_dimension):
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
        values = values[:, :, 0] * num_splits_per_dimension * num_splits_per_dimension + values[:, :, 1] * num_splits_per_dimension + values[:, :, 2]
        # Round the values, s.t. derivations are put back to their closest index.
        return np.round(values)

    @staticmethod
    def import_objects(filepath, cached_objects=None, **kwargs):
        """ Import all objects for the given file and returns the loaded objects

        In .obj files a list of objects can be saved in.
        In .ply files only one object can saved so the list has always at most one element

        :param filepath: the filepath to the location where the data is stored
        :param cached_objects: a dict of filepath to objects, which have been loaded before, to avoid reloading (the dict is updated in this function)
        :param kwargs: all other params are handed directly to the bpy loading fct. check the corresponding documentation
        :return: a list of all newly loaded objects, in the failure case an empty list is returned
        """
        if os.path.exists(filepath):
            if cached_objects is not None and isinstance(cached_objects, dict):
                if filepath in cached_objects.keys():
                    created_obj = []
                    for obj in cached_objects[filepath]:
                        # deselect all objects and duplicate the object
                        bpy.ops.object.select_all(action='DESELECT')
                        obj.select_set(True)
                        bpy.ops.object.duplicate()
                        # save the duplicate in new list
                        if len(bpy.context.selected_objects) != 1:
                            raise Exception("The amount of objects after the copy was more than one!")
                        created_obj.append(bpy.context.selected_objects[0])
                    return created_obj
                else:
                    loaded_objects = Utility.import_objects(filepath, cached_objects=None, **kwargs)
                    cached_objects[filepath] = loaded_objects
                    return loaded_objects
            else:
                # save all selected objects
                previously_selected_objects = set(bpy.context.selected_objects)
                if filepath.endswith('.obj'):
                    # load an .obj file:
                    bpy.ops.import_scene.obj(filepath=filepath, **kwargs)
                elif filepath.endswith('.ply'):
                    # load a .ply mesh
                    bpy.ops.import_mesh.ply(filepath=filepath, **kwargs)
                    # add a default material to ply file
                    mat = bpy.data.materials.new(name="ply_material")
                    mat.use_nodes = True
                    loaded_objects = list(set(bpy.context.selected_objects) - previously_selected_objects)
                    for obj in loaded_objects:
                        obj.data.materials.append(mat)

                # return all currently selected objects
                return list(set(bpy.context.selected_objects) - previously_selected_objects)
        else:
            raise Exception("The given filepath does not exist: {}".format(filepath))

    @staticmethod
    def add_output_entry(output):
        """ Registers the given output in the scene's custom properties

        :param output: A dict containing key and path of the new output type.
        """
        if GlobalStorage.is_in_storage("output"):
            if not Utility.output_already_registered(output, GlobalStorage.get("output")): # E.g. multiple camera samplers
                GlobalStorage.get("output").append(output)
        else:
            GlobalStorage.set("output", [output])

    @staticmethod
    def register_output(output_dir, prefix, key, suffix, version, unique_for_camposes=True):
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
    def find_registered_output_by_key(key):
        """ Returns the output which was registered with the given key.

        :param key: The output key to look for.
        :return: The dict containing all information registered for that output. If no output with the given key exists, None is returned.
        """
        if GlobalStorage.is_in_storage("output"):
            for output in GlobalStorage.get("output"):
                if output["key"] == key:
                    return output

        return None

    @staticmethod
    def output_already_registered(output, output_list):
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
