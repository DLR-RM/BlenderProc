import os

import bpy

from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.types.MeshObjectUtility import MeshObject, create_primitive


class RockEssentialsGroundConstructor(LoaderInterface):
    """
    Constructs a ground plane with a material using RE PBR Rock Shader.

    Example 1: Construct a scaled ground plane with 30 subdivision cuts, custom name and subdiv level value for
    rendering using PBR Rock Shader from the specified .blend file.

    .. code-block:: yaml

        {
          "module": "constructor.RockEssentialsGroundConstructor",
          "config": {
            "tiles": [
            {
              "shader_path": "<args:0>/Rock Essentials/Individual Rocks/Volcanic/Rocks_Volcanic_Small.blend",
              "plane_scale": [50, 50, 1],
              "subdivision_cuts": 30,
              "subdivision_render_levels": 2,
              "tile_name": "Gr_Plane_1"
            }
            ]
          }
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - tiles
          - Ground tiles to create, each cell contains a separate tile configuration.
          - list

    **Ground plane properties**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - shader_path
          - Path to a .blend file that containing PBR Rock Shader in //NodeTree// section.
          - string
        * - plane_scale
          - Scale of a ground plane. Default: [10, 10, 1].
          - mathutils.Vector/list
        * - subdivision_cuts
          - Amount of cuts along each plane axis. Default: 50.
          - int
        * - subdivision_render_levels
          - Render level for a plane's subdivision modifier. Default: 3.
          - int
        * - tile_name
          - Name of the ground tile. Set one if you plan to use this module multiple times in one config. Default:
            'RE_ground_plane'.
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        """ Constructs a ground plane.
            1. Get configuration parameters.
            2. Load shader.
            3. Construct ground plane and it's material node tree.
        """

        tiles = self.config.get_list("tiles")
        for tile in tiles:
            if tile:
                ground_config = Config(tile)
                self._load_shader(ground_config)
                self._construct_ground_plane(ground_config)

    def _load_shader(self, ground_config):
        """ Loads PBR Rock Shader

        :param ground_config: Config object that contains user-defined settings for ground plane. Type: Config.
        """
        shader_path = ground_config.get_string("shader_path")
        bpy.ops.wm.append(filepath=os.path.join(shader_path, "/NodeTree", "", "PBR Rock Shader"),
                          filename="PBR Rock Shader", directory=os.path.join(shader_path+"/NodeTree"))

    def _construct_ground_plane(self, ground_config):
        """ Constructs a ground plane.

        :param ground_config: Config object that contains user-defined settings for ground plane. Type: Config.
        """
        # get scale\'size' of a plane to be created 10x10 if not defined
        plane_scale = ground_config.get_vector3d("plane_scale", [1, 1, 1])
        # get the amount of subdiv cuts, 50 (50x50=250 segments) if not defined
        subdivision_cuts = ground_config.get_int("subdivision_cuts", 50)
        # get the amount of subdiv render levels, 2 if not defined
        subdivision_render_levels = ground_config.get_int("subdivision_render_levels", 3)
        # get name, 'RE_ground_plane' if not defined
        tile_name = ground_config.get_string("tile_name", "RE_ground_plane")

        # create new plane, set its size
        plane_obj = create_primitive("PLANE")
        plane_obj.set_name(tile_name)
        plane_obj.set_scale(plane_scale)

        # create new material
        mat_obj = plane_obj.new_material("re_ground_mat")

        # delete Principled BSDF node
        mat_obj.remove_node(mat_obj.get_the_one_node_with_type("BsdfPrincipled"))

        # create PBR Rock Shader, connect its output 'Shader' to the Material Output nodes input 'Surface'
        group_pbr = mat_obj.new_node("ShaderNodeGroup")
        group_pbr.node_tree = bpy.data.node_groups['PBR Rock Shader']
        output_node = mat_obj.get_the_one_node_with_type('OutputMaterial')
        mat_obj.link(group_pbr.outputs['Shader'], output_node.inputs['Surface'])

        # create Image Texture nodes for color, roughness, reflection, and normal maps
        self._create_node(mat_obj, 'color', 'Color')
        self._create_node(mat_obj, 'roughness', 'Roughness')
        self._create_node(mat_obj, 'reflection', 'Reflection')
        self._create_node(mat_obj, 'normal', 'Normal')

        # create subsurface and displacement modifiers
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=subdivision_cuts)
        bpy.ops.object.modifier_add(type="DISPLACE")
        bpy.ops.object.modifier_add(type="SUBSURF")

        # create new texture
        texture_name = tile_name + "_texture"
        bpy.data.textures.new(name=texture_name, type="IMAGE")

        # set new texture as a displacement texture, set UV texture coordinates
        plane_obj.blender_obj.modifiers['Displace'].texture = bpy.data.textures[texture_name]
        plane_obj.blender_obj.modifiers['Displace'].texture_coords = 'UV'

        bpy.ops.object.editmode_toggle()
        # scale, set render levels for subdivision, strength of displacement and set passive rigidbody state
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.context.object.modifiers["Subdivision"].render_levels = subdivision_render_levels
        plane_obj.set_cp("physics", False)
        self._set_properties([plane_obj])

    def _create_node(self, mat_obj: Material, map_type: str, in_point: str):
        """ Handles the creation a ShaderNodeTexImage node, setting maps and creating links.

        :param mat_obj: The material object.
        :param map_type: Type of image/map that will be assigned to this node.
        :param in_point: Name of an input point in PBR Rock Shader node to use.
        """
        new_node = mat_obj.new_node('ShaderNodeTexImage')
        # set output point of the node to connect
        output_socket = new_node.outputs['Color']
        new_node.label = map_type
        # special case for a normal map since the link between TextureNode and PBR RS is broken with Normal Map node
        if map_type == 'normal':
            # create new node
            group_norm_map = mat_obj.new_node('ShaderNodeNormalMap')
            # connect color output/input
            mat_obj.link(new_node.outputs['Color'], group_norm_map.inputs['Color'])
            # redefine main output point to connect
            output_socket = group_norm_map.outputs['Normal']
        # select main input point of the PBR Rock Shader
        group_input_socket = mat_obj.nodes.get("Group").inputs[in_point]
        mat_obj.link(output_socket, group_input_socket)
