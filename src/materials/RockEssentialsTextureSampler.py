import bpy
import os
import re
from random import randint

from src.loader.Loader import Loader
from src.utility.Config import Config
from src.utility.Utility import Utility


class RockEssentialsTextureSampler(Loader):
    """ Samples a random texture data from the provided list and sets the images to each selected object if they have a RE-specific material applied.

    **Ground plane config**:

    .. csv-table::
       :header: "Keyword", "Description"

       "selector", "Use a getter.Entity provider to select objects (ground planes) with RE-specific material applied."
       "texture", "A list of dicts with texture data: images, path to the images, etc."

     **Texture data**:

    The maximum expected amount of images for a texture is 5: four for the material (color, roughness, reflection, and
    normal) and one for the displacement modifier (displacement), but the least required amount of images to create a
    visible difference in the scene is one: color. Thus at least provide a color map for each texture.

    .. csv-table::
       :header: "Keyword", "Description"

       "path", "Path to a directory containing maps required for recreating texture. Type: string."
       "images/color", "Full name of a color map image. Optional. Type: string."
       "images/roughness", "Full name of a roughness map image. Optional. Type: string."
       "images/reflection", "Full name of a reflection map image. Optional. Type: string."
       "images/normal", "Full name of a normal map image. Optional. Type: string."
       "images/displacement", "Full name of a displacement map image. Optional. Type: string."
    """

    def __init__(self, config):
        Loader.__init__(self, config)
        # set a RE-specific material name pattern to look for in the selected objects
        self.target_material = "re_ground_mat.*"

    def run(self):
        """ Sets a random texture from the provided list for each selected object if it has a re-selected material applied. """
        # get list of textures
        textures = self.config.get_list("textures")
        # get objects to set textures to. It is implied that one is selecting the ground planes by the name that was
        # defined in the config of the constructor.RockEssentialsGroundConstructor config
        ground_tiles = self.config.get_list("selector", [])
        # for each selected ground tile (plane)
        for ground_tile in ground_tiles:
            # get a random texture
            selected_texture = self._get_random_texture(textures)
            # load the images
            images, uv_scaling = self._load_images(selected_texture)
            # set images
            self._set_textures(ground_tile, images, uv_scaling)

    def _get_random_texture(self, textures):
        """ Chooses a random texture data from the provided list.

        :param textures: List of dicts. Each dict is describing a texture data (path to images, images, etc.).
        :return: A config object of the selected texture dict.
        """
        selected_idx = randint(0, len(textures) - 1)
        selected_texture = Config(textures[selected_idx])

        return selected_texture

    def _load_images(self, selected_texture):
        """ Loads images that are used as color, roughness, reflection, normal, and displacement maps.

        :param selected_texture: Config object that contains .
        :return: Dict of format {map type: image obj}.
        """
        loaded_images = {}
        # get path to image folder
        path = selected_texture.get_string("path")
        # get uv layer scaling
        uv_scaling = selected_texture.get_float("uv_scaling", 1)
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

        return loaded_images, uv_scaling

    def _set_textures(self, ground_tile, images, uv_scaling):
        """ Sets available loaded images to a texture of a current processed ground tile.

        :param ground_tile: Ground tile (plane) object.
        :param images: Dict of loaded images of a chosen texture.
        :param uv_scaling: Scaling factor for the UV layer of the tile.
        """
        # get a target material in case ground tile has more than one
        for material in ground_tile.data.materials.items():
            if re.fullmatch(self.target_material, material[0]):
                mat_obj = bpy.data.materials[material[0]]
            else:
                raise Exception("No re material " + self.target_material + " found in selected objects. Check if "
                                                                           "constructor.RockEssentialsGroundConstructor"
                                                                           " module at least one ground tile!")
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

        # and scale the texture
        for point in ground_tile.data.uv_layers.active.data[:]:
            point.uv = point.uv * uv_scaling
