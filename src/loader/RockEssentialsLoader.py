import bpy
import os

from src.loader.Loader import Loader
from src.utility.Config import Config
from src.utility.Utility import Utility


class RockEssentialsLoader(Loader):
    """
    **Properties per rock batch**:

    .. csv-table::
       :header: "Keyword", "Description"

       "path", "Path to a .blend file containing desired rock/cliff objects in //Object// section. Type: string."
       "objects", "List of rock-/cliff-object names to be loaded. Type: list. Optional. Default value: []. If not specified amount property is used for consequential loading."
       "amount", "Amount of rock-/cliff-object to load. Type: int. Optional. Default value: 0. If not specified amount will be eventually set to the amount of suitable objects in the current section of a blend file."
       "render_levels", "Number of subdivisions to perform when rendering. Type: int. Optional. Default value: 3."
       "high_detail_mode", "Flag for enabling HDM when possible. Type: boolean. Optional. Default value: False."
       "physics", "Custom property for physics/rigidbody state. Type: bool Optional. Default value: False."

    **Ground plane properties**:

    .. csv-table::
       :header: "Keyword", "Description"

       "shader_path", "Path to a .blend file that containing PBR Rock Shader in //NodeTree// section. Type: string."
       "images/image_path", "Path to a directory containing maps required for recreating texture. Type: string."
       "images/maps/color", "Full name of a color map image. Type: string."
       "images/maps/glossy", "Full name of a roughness/glossiness map image. Type: string."
       "images/maps/reflection", "Full name of a reflection map image. Type: string."
       "images/maps/normal", "Full name of a normal map image. Type: string."
       "images/maps/displacement", "Full name of a displacement map image. Type: string."
       "plane_scale", "Scale of a ground plane. Type: mathutils Vector/list. Optional. Default value: [10, 10, 1]"
       "subdivision_cuts", "Amount of cuts along each plane axis. Type: int. Optional. Default value: 50."
       "subdivision_render_levels", "Render level for a plane's subdivision modifier. Type: int. Optional. Default value: 3."
       "displacement_strength", "Strength of a plane's displacement modifier. Type: float. Optional. Default value: 1."
    """

    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):
        """ Loads rocks and constructs ground plane. """
    
        rocks_settings = self.config.get_list("rocks", [])
        for subsec_num, subsec_settings in enumerate(rocks_settings):
            subsec_config = Config(subsec_settings)
            subsec_objects = self._load_rocks(subsec_num, subsec_config)
            self._set_rocks_properties(subsec_objects, subsec_config)

        ground_settings = self.config.get_raw_dict("ground", {})
        if ground_settings:
            ground_config = Config(ground_settings)
            self._load_shader(ground_config)
            loaded_images = self._load_images(ground_config)
            self._construct_ground_plane(loaded_images, ground_config)

    def _load_rocks(self, subsec_num, subsec_config):
        """ Loads rocks.

        :param subsec_num: Number of a corresponding cell (batch) in `rocks` list in configuration. Used for name generation.
        :param subsec_config: Config object that contains user-defined settings for a current batch.
        :return: List of loaded objects.
        """
        loaded_objects = []
        obj_types = ["Rock", "Cliff"]
        # get path to .blend file
        path = subsec_config.get_string("path")
        # get list of obj names, empty if not defined
        objects = subsec_config.get_list("objects", [])
        # get amount of rocks in this batch, 0 if not defined
        amount = subsec_config.get_int("amount", 0)

        obj_list = []
        with bpy.data.libraries.load(path) as (data_from, data_to):
            # if list of names is empty
            if not objects:
                # get list of rocks suitable for loading - objects that are rocks or cliffs
                for obj_type in obj_types:
                    obj_list += [obj for obj in data_from.objects if obj_type in obj]
            else:
                # if names are defined - get those that are available in this .blend file
                obj_list = [obj for obj in data_from.objects if obj in objects]
        # if amount of rocks to be loaded is zero (default value) - set amount such that every rock is loaded once
        if amount == 0:
            amount = len(obj_list)

        for i in range(amount):
            # load rock
            obj = obj_list[i % len(obj_list)]
            bpy.ops.wm.append(filepath=os.path.join(path, "/Object", obj), filename=obj,
                              directory=os.path.join(path+"/Object"))
            loaded_obj = bpy.context.scene.objects[obj]
            # set custom name for easier tracking in the scene
            bpy.context.scene.objects[obj].name = obj + "_" + str(subsec_num) + "_" + str(i)
            # append to return list
            loaded_objects.append(loaded_obj)

        return loaded_objects
    
    def _set_rocks_properties(self, objects, subsec_config):
        """ Sets rocks properties in accordance to user-defined values.

        :param objects: List of objects.
        :param subsec_config: Config object that contains user-defined settings for a current batch.
        """
        # get physics custom setting, 'passive' if not defined
        physics = subsec_config.get_bool("physics", False)
        # get render level for a batch, '3' if not defined
        render_levels = subsec_config.get_int("render_levels", 3)
        # get HDM custom setting for a batch, 'disabled'\'False' if not defined
        high_detail_mode = subsec_config.get_bool("high_detail_mode", False)
    
        for obj in objects:
            # set physics parameter
            obj["physics"] = physics
            # set render value
            obj.modifiers["Subsurf"].render_levels = render_levels
            # if HDM is enabled
            if "01) High Detail Mode" in obj:
                obj["01) High Detail Mode"] = high_detail_mode
            else:
                print("High Detail Mode is unavailable for " + str(obj.name) + ", omitting.")

    def _load_shader(self, ground_config):
        """ Loads PBR Rock Shader

        :param ground_config: Config object that contains user-defined settings for ground plane.
        """
        shader_path = ground_config.get_string("shader_path")
        bpy.ops.wm.append(filepath=os.path.join(shader_path, "/NodeTree", "", "PBR Rock Shader"),
                          filename="PBR Rock Shader", directory=os.path.join(shader_path+"/NodeTree"))

    def _load_images(self, ground_config):
        """ Loads images that are used as color, roughness, reflection, normal, and displacement maps.

        :param ground_config: Config object that contains user-defined settings for ground plane.
        :return: Dict of format {map type: image obj}.
        """
        loaded_images = {}
        # get path to image folder
        path = ground_config.get_string("images/image_path")
        # get dict of format {may type: full map name}
        maps = ground_config.get_raw_dict("images/maps")
        # check if dict contains all required maps
        if len(maps) == 5:
            for key, value in maps.items():
                # open image
                bpy.ops.image.open(filepath=os.path.join(path + value), directory=path)
                # if map type is not 'color' - set colorspace to 'Non-Color'
                if key != "color":
                    bpy.data.images[value].colorspace_settings.name = 'Non-Color'

                # update return dict
                loaded_images.update({key: bpy.data.images.get(value)})
        else:
            raise Exception("Maps missing. Must define color, glossy, reflection, normal, and displacement maps.")

        return loaded_images

    def _construct_ground_plane(self, loaded_images, ground_config):
        """ Constructs ground plane.

        :param loaded_images: Dict of format {map type: image obj}
        :param ground_config: Config object that contains user-defined settings for ground plane.
        """
        # get scale\'size' of a plane to be created 10x10 if not defined
        plane_scale = ground_config.get_vector3d("plane_scale", [10, 10, 1])
        # get the amount of subdiv cuts, 50 (50x50=250 segments) if not defined
        subdivision_cuts = ground_config.get_int("subdivision_cuts", 50)
        # get the amount of subdiv render levels, 2 if not defined
        subdivision_render_levels = ground_config.get_int("subdivision_render_levels", 3)
        # get displacement strength, 1 if not defined
        displacement_strength = ground_config.get_float("displacement_strength", 1)

        # create new plane, set its size
        bpy.ops.mesh.primitive_plane_add()
        plane_obj = bpy.data.objects["Plane"]
        plane_obj.scale = plane_scale

        # create new material, enable use of nodes
        mat_obj = bpy.data.materials.new(name="plane_mat")
        mat_obj.use_nodes = True

        # set material
        plane_obj.data.materials.append(mat_obj)
        nodes = mat_obj.node_tree.nodes
        links = mat_obj.node_tree.links

        # delete Principled BSDF node
        nodes.remove(nodes["Principled BSDF"])

        # create PBR Rock Shader, connect its output 'Shader' to the Material Output nodes input 'Surface'
        group_pbr = nodes.new("ShaderNodeGroup")
        group_pbr.node_tree = bpy.data.node_groups['PBR Rock Shader']
        output_node = nodes.get("Material Output")
        links.new(group_pbr.outputs['Shader'], output_node.inputs['Surface'])

        # create Image Texture node, set color map
        self._create_node(nodes, links, loaded_images, 'color',  'Color')
        # create Image Texture node, set glossy map
        self._create_node(nodes, links, loaded_images, 'roughness', 'Roughness')
        # create Image Texture node, set reflection map
        self._create_node(nodes, links, loaded_images, 'reflection', 'Reflection')
        # create Image Texture node, set normal map
        self._create_node(nodes, links, loaded_images, 'normal', 'Normal')

        # create subsurface and displacement modifiers
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=subdivision_cuts)
        bpy.ops.object.modifier_add(type="SUBSURF")
        bpy.ops.object.modifier_add(type="DISPLACE")

        # create new texture, set map
        bpy.ops.texture.new()
        bpy.data.textures['Texture'].image = loaded_images['displacement']

        # set new texture as a displacement texture, set UV texture coordinates
        plane_obj.modifiers['Displace'].texture = bpy.data.textures['Texture']
        plane_obj.modifiers['Displace'].texture_coords = 'UV'

        bpy.ops.object.editmode_toggle()
        # scale, set render levels for subdivision, strength of displacement and set passive rigidbody state
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.context.object.modifiers["Subdivision"].render_levels = subdivision_render_levels
        bpy.context.object.modifiers["Displace"].strength = displacement_strength
        plane_obj["physics"] = False

    def _create_node(self, nodes, links, loaded_images, map_type, in_point):
        """ Handles creating a ShaderNodeTexImage node, setting maps and creating links.

        :param nodes: All nodes in the node tree of the material object.
        :param links: All links in the node tree of the material object.
        :param loaded_images: Dict of loaded images/maps.
        :param map_type: Type of image/map to set.
        :param in_point: Name of an input point in PBR Rock Shader node to use.
        """
        nodes.new('ShaderNodeTexImage')
        # magic: last created node, set map
        nodes[-1].image = loaded_images[map_type]
        # set output point of the node to connect - 'Color' in all cases except when setting normal map
        a = nodes.get(nodes[-1].name).outputs['Color']
        # special case for a normal map since the link between TextureNode and PBR RS is broken with Normal Map node
        if map_type == 'normal':
            # create new node
            group_norm_map = nodes.new('ShaderNodeNormalMap')
            # magic: pre-last node, select Color output
            a_norm = nodes.get(nodes[-2].name).outputs['Color']
            # select input point
            b_norm = group_norm_map.inputs['Color']
            # connect them
            links.new(a_norm, b_norm)
            # redefine main output point to connect
            a = nodes.get(nodes[-1].name).outputs['Normal']

        # select main input point of the PBR Rock Shader
        b = nodes.get("Group").inputs[in_point]
        links.new(a, b)
