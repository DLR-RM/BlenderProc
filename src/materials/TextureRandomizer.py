from src.main.Module import Module
import bpy
import numpy as np


class TextureRandomizer(Module):

    """
    For a scene randomizes the textures for the objects. The amount of randomization depends
    on the randomization level (0 - 1).
    Randomization level => Expected fraction of objects for which the texture should be randomized

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "randomization_level", "Level of randomization, greater the value greater the randomization.
       Allowed values are [0-1]"
    """

    def __init__(self, config):

        Module.__init__(self, config)
        self.randomization_level = self.config.get_float("randomization_level")
        self.texture_images = []

    def run(self):

        self._store_all_textures()

        self._randomize_textures_in_scene()

    def _randomize_textures_in_scene(self):

        """
        Randomizes the textures in a loaded scene

        """

        for obj in bpy.context.scene.objects:

            self._randomize_texture(obj)

    def _randomize_texture(self, obj):

        """
        For the given object with randomization_level probability assigns a random texture from the scene

        :param obj: Object for which texture should be randomized
        """

        for m in obj.material_slots:

            if np.random.uniform(0, 1) > self.randomization_level:
                return

            nodes = m.material.node_tree.nodes
            image_node = nodes.get("Image Texture")

            if image_node is not None and image_node.image is not None:

                random_index = np.random.random_integers(0, len(self.texture_images) - 1)
                image_node.image = self.texture_images[random_index]

    def _store_all_textures(self):
        """
        Stores all available textures in the scene

        """

        for obj in bpy.context.scene.objects:

            for m in obj.material_slots:

                nodes = m.material.node_tree.nodes
                image_node = nodes.get("Image Texture")

                if image_node is not None and image_node.image is not None:
                    self.texture_images.append(image_node.image.copy())
