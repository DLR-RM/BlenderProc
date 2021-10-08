import os
import re
from random import choice

import bpy

from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.utility.Utility import Utility


class RockEssentialsTextureSampler(LoaderInterface):
    """
    Samples a random texture data from the provided list and sets the images to each selected object (ground tiles
    created by constructor.RockEssentialsGroundConstructor) if they have a RE-specific material assigned (they have
    it applied by default if ground tile was constructed by aforementioned constructor module).

    Example 1: For all ground planes matching a name pattern select a random set of textures with custom ambient
    occlusion, displacements strength and UV map scaling factor values.

    .. code-block:: yaml

        {
          "module": "materials.RockEssentialsTextureSampler",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": "Gr_Plane.*",
                "type": "MESH"
              }
            },
            "textures": [
            {
              "path": "<args:0>/Rock Essentials/Ground Textures/Pebbles/RDTGravel001/",
              "uv_scaling": 2,
              "ambient_occlusion": [0.5, 0.5, 0.5, 1],
              "displacement_strength": 1.5,
              "images": {
                "color": "RDTGravel001_COL_VAR1_3K.jpg",
                "roughness": "RDTGravel001_GLOSS_3K.jpg",
                "reflection": "RDTGravel001_REFL_3K.jpg",
                "normal": "RDTGravel001_NRM_3K.jpg",
                "displacement": "RDTGravel001_DISP16_3K.tif"
              }
            },
            {
              "path": "<args:0>/Rock Essentials/Ground Textures/Pebbles/RDTGroundForest002/",
              "uv_scaling": 4,
              "ambient_occlusion": [0.7, 0.7, 0.7, 1],
              "displacement_strength": 0.5,
              "images": {
                "color": "RDTGroundForest002_COL_VAR1_3K.jpg",
                "roughness": "RDTGroundForest002_GLOSS_3K.jpg",
                "reflection": "RDTGroundForest002_REFL_3K.jpg",
                "normal": "RDTGroundForest002_NRM_3K.jpg",
                "displacement": "RDTGroundForest002_DISP16_3K.tif"
              }
            }
            ]
          }
        }

    **Ground plane config**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - selector
          - Objects (ground planes) with RE-specific material applied.
          - Provider
        * - textures
          - A list of dicts with texture data: images, path to the images, etc.
          - list

    **Texture data**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - path
          - Path to a directory containing maps required for recreating texture.
          - string
        * - ambient_occlusion
          - Ambient occlusion [R, G, B, A] color vector for a ground tile material's shader. Default: [1, 1, 1, 1].
          - mathutils.Vector
        * - uv_scaling
          - Scaling factor of the UV map. Default: 1.
          - float
        * - displacement_strength
          - Strength of a plane's displacement modifier. Default: 1.
          - float
        * - images/color
          - Full name of a color map image.
          - string
        * - images/roughness
          - Full name of a roughness map image.
          - string
        * - images/reflection
          - Full name of a reflection map image.
          - string
        * - images/normal
          - Full name of a normal map image.
          - string
        * - images/displacement
          - Full name of a displacement map image.
          - string
    """

    def __init__(self, config):
        LoaderInterface.__init__(self, config)
        # set a RE-specific material name pattern to look for in the selected objects
        self.target_material = "re_ground_mat.*"

    def run(self):
        """ Sets a random texture from the provided list for each selected object if it has a re-material assigned.
            1. For all selected ground tiles.
            2. Get a random texture from the defined list.
            3. Load images.
            4. Assign them to a material.
        """
        # get list of textures
        textures = self.config.get_list("textures")
        # get objects to set textures to. It is implied that one is selecting the ground planes by the name that was
        # defined in the config of the constructor.RockEssentialsGroundConstructor config
        ground_tiles = self.config.get_list("selector")
        # for each selected ground tile (plane)
        for ground_tile in ground_tiles:
            # get a random texture
            selected_texture = self._get_random_texture(textures)
            # load the images
            images, uv_scaling, ambient_occlusion, displacement_strength = self._load_images(selected_texture)
            # set images
            self._set_textures(ground_tile, images, uv_scaling, ambient_occlusion, displacement_strength)

    def _get_random_texture(self, textures):
        """ Chooses a random texture data from the provided list.

        :param textures: Texture data. Type: list.
        :return: Selected texture data. Type: Config.
        """
        selected_dict = choice(textures)
        selected_texture = Config(selected_dict)

        return selected_texture

    def _load_images(self, selected_texture):
        """ Loads images that are used as color, roughness, reflection, normal, and displacement maps.

        :param selected_texture: Selected texture data. Type: Config.
        :return: loaded_images: Loaded images. Type: dict.
        :return: uv_scaling: Scaling factor of the UV map. Type: float.
        :return: ambient_occlusion: Ambient occlusion color vector. Type: mathutils.Vector.
        :return: displacement_strength: Strength of a plane's displacement modifier. Type: float.
        """
        loaded_images = {}
        # get path to image folder
        path = selected_texture.get_string("path")
        # get uv layer scaling factor
        uv_scaling = selected_texture.get_float("uv_scaling", 1)
        # get ambient occlusion vector
        ambient_occlusion = selected_texture.get_list("ambient_occlusion", [1, 1, 1, 1])
        # get displacement modifier strength
        displacement_strength = selected_texture.get_float("displacement_strength", 1)
        # get dict of format {may type: full map name}
        maps = selected_texture.get_raw_dict("images")
        # check if dict contains all required maps
        for key, value in maps.items():
            # open image
            bpy.ops.image.open(filepath=os.path.join(path + value), directory=path)
            # if map type is not 'color' - set colorspace to 'Non-Color'
            if key != "color":
                bpy.data.images[value].colorspace_settings.name = 'Non-Color'

            # update return dict
            loaded_images.update({key: bpy.data.images.get(value)})

        return loaded_images, uv_scaling, ambient_occlusion, displacement_strength

    def _set_textures(self, ground_tile, images, uv_scaling, ambient_occlusion, displacement_strength):
        """ Sets available loaded images to a texture of a current processed ground tile.

        :param ground_tile: Ground tile (plane). Type: bpy.types.Object.
        :param images: Loaded images of a chosen texture. Type: dict.
        :param uv_scaling: Scaling factor for the UV layer of the tile. Type: float.
        """
        # get a target material in case ground tile has more than one
        for material in ground_tile.data.materials.items():
            if re.fullmatch(self.target_material, material[0]):
                mat_obj = bpy.data.materials[material[0]]
            else:
                raise Exception("No RE material " + self.target_material + " found in selected objects. Check if "
                                "constructor.RockEssentialsGroundConstructor module was run at least once and created "
                                "at least one ground tile!")

        # get the node tree of the current material
        nodes = mat_obj.node_tree.nodes
        # get all Image Texture nodes in the tree
        image_texture_nodes = Utility.get_nodes_with_type(nodes, 'ShaderNodeTexImage')
        # for each Image Texture node set a texture (image) if one was loaded
        for node in image_texture_nodes:
            if node.label in images.keys():
                node.image = images[node.label]

        # get texture name for a displacement modifier of the current ground tile
        texture_name = ground_tile.name + "_texture"
        # if displacement map (image) was provided and loaded - set it to the modifier
        if "displacement" in images.keys():
            bpy.data.textures[texture_name].image = images['displacement']

        # set ambient occlusion
        nodes.get("Group").inputs["AO"].default_value = ambient_occlusion

        # set displacement modifier strength
        bpy.context.object.modifiers["Displace"].strength = displacement_strength

        # and scale the texture
        for point in ground_tile.data.uv_layers.active.data[:]:
            point.uv = point.uv * uv_scaling
