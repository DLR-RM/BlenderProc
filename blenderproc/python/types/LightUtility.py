from typing import Union

import bpy

from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.utility.Utility import Utility, KeyFrame
from mathutils import Color
import numpy as np


class Light(Entity):
    def __init__(self, type: str = "POINT", name: str = "light", blender_obj: bpy.types.Light = None):
        """
        Constructs a new light if no blender_obj is given, else the params type and name are used to construct a new
        light.

        :param type: The initial type of light, can be one of [POINT, SUN, SPOT, AREA].
        :param name: The name of the new light
        :param blender_obj: A bpy.types.Light, this is then used instead of the type and name.
        """
        if blender_obj is None:
            # this create a light object and sets is as the used entity inside of the super class
            light_data = bpy.data.lights.new(name=name, type=type)
            light_obj = bpy.data.objects.new(name=name, object_data=light_data)
            bpy.context.collection.objects.link(light_obj)
            super(Light, self).__init__(light_obj)
        else:
            super(Light, self).__init__(blender_obj)

    def set_energy(self, energy: float, frame: int = None):
        """ Sets the energy of the light.

        :param energy: The energy to set. If the type is SUN this value is interpreted as Watt per square meter, otherwise it is interpreted as Watt.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.data.energy = energy
        Utility.insert_keyframe(self.blender_obj.data, "energy", frame)

    def set_color(self, color: Union[list, Color], frame: int = None):
        """ Sets the color of the light.

        :param color: The rgb color to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.data.color = color
        Utility.insert_keyframe(self.blender_obj.data, "color", frame)

    def set_distance(self, distance: float, frame: int = None):
        """ Sets the falloff distance of the light = point where light is half the original intensity.

        :param distance: The falloff distance to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.data.distance = distance
        Utility.insert_keyframe(self.blender_obj.data, "distance", frame)

    def set_type(self, type: str, frame: int = None):
        """ Sets the type of the light.

        :param type: The type to set, can be one of [POINT, SUN, SPOT, AREA].
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.blender_obj.data.type = type
        Utility.insert_keyframe(self.blender_obj.data, "type", frame)

    def setup_as_projector(self, pattern: np.ndarray, frame: int = None):
        """ Sets a spot light source as projector of a pattern image. Sets location and angle of projector to current
        camera. Adjusts scale of pattern image to fit field-of-view of camera:
        $(0.5 + \frac{X}{Z \cdot F}, 0.5 + \frac{X}{Z \cdot F \cdot r}, 0)$
        where $F$ is focal length and $r$ aspect ratio.
        WARNING: This should be done after the camera parameters are set!

        :param pattern: pattern image to be projected onto scene as np.ndarray.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        cam_ob = bpy.context.scene.camera
        fov = cam_ob.data.angle     # field of view of current camera in radians

        focal_length = 2 * np.tan(fov / 2)
        # Image aspect ratio = height / width
        aspect_ratio = bpy.context.scene.render.resolution_y / bpy.context.scene.render.resolution_x

        # Set location of light source to camera -- COPY TRANSFORMS
        self.blender_obj.constraints.new('COPY_TRANSFORMS')
        self.blender_obj.constraints['Copy Transforms'].target = cam_ob

        # Setup nodes for projecting image
        self.blender_obj.data.use_nodes = True
        self.blender_obj.data.shadow_soft_size = 0
        self.blender_obj.data.spot_size = 3.14159  # 180deg in rad
        self.blender_obj.data.cycles.cast_shadow = False

        nodes = self.blender_obj.data.node_tree.nodes
        links = self.blender_obj.data.node_tree.links

        node_ox = nodes.get('Emission')

        image_data = bpy.data.images.new('pattern', width=pattern.shape[1], height=pattern.shape[0], alpha=True)
        image_data.pixels = pattern.ravel()

        # Set Up Nodes
        node_pattern = nodes.new(type="ShaderNodeTexImage")  # Texture Image
        node_pattern.label = 'Texture Image'
        node_pattern.image = bpy.data.images['pattern']
        node_pattern.extension = 'CLIP'

        node_coord = nodes.new(type="ShaderNodeTexCoord")  # Texture Coordinate
        node_coord.label = 'Texture Coordinate'

        f_value = nodes.new(type="ShaderNodeValue")
        f_value.label = 'Focal Length'
        f_value.outputs[0].default_value = focal_length

        fr_value = nodes.new(type="ShaderNodeValue")
        fr_value.label = 'Focal Length * Ratio'
        fr_value.outputs[0].default_value = focal_length * aspect_ratio

        divide1 = nodes.new(type="ShaderNodeMath")
        divide1.label = 'X / ZF'
        divide1.operation = 'DIVIDE'

        divide2 = nodes.new(type="ShaderNodeMath")
        divide2.label = 'Y / ZFr'
        divide2.operation = 'DIVIDE'

        multiply1 = nodes.new(type="ShaderNodeMath")
        multiply1.label = 'Z * F'
        multiply1.operation = 'MULTIPLY'

        multiply2 = nodes.new(type="ShaderNodeMath")
        multiply2.label = 'Z * Fr'
        multiply2.operation = 'MULTIPLY'

        center_image = nodes.new(type="ShaderNodeVectorMath")
        center_image.operation = 'ADD'
        center_image.label = 'Offset'
        center_image.inputs[1].default_value[0] = 0.5
        center_image.inputs[1].default_value[1] = 0.5

        xyz_components = nodes.new(type="ShaderNodeSeparateXYZ")

        combine_xyz = nodes.new(type="ShaderNodeCombineXYZ")

        # Set Up Links
        links.new(node_pattern.outputs["Color"], node_ox.inputs["Color"])  # Link Image Texture to Emission
        links.new(node_coord.outputs["Normal"], xyz_components.inputs["Vector"])
        # ZF
        links.new(f_value.outputs[0], multiply1.inputs[1])
        links.new(xyz_components.outputs["Z"], multiply1.inputs[0])
        # ZFr
        links.new(fr_value.outputs[0], multiply2.inputs[1])
        links.new(xyz_components.outputs["Z"], multiply2.inputs[0])
        # X / ZF
        links.new(xyz_components.outputs["X"], divide1.inputs[0])
        links.new(multiply1.outputs[0], divide1.inputs[1])
        # Y / ZFr
        links.new(xyz_components.outputs["Y"], divide2.inputs[0])
        links.new(multiply2.outputs[0], divide2.inputs[1])
        # Combine (X/ZF, Y/ZFr, 0)
        links.new(divide1.outputs[0], combine_xyz.inputs["X"])
        links.new(divide2.outputs[0], combine_xyz.inputs["Y"])
        # Center image by offset
        links.new(combine_xyz.outputs["Vector"], center_image.inputs[0])
        # Link Mapping to Image Texture
        links.new(center_image.outputs["Vector"], node_pattern.inputs["Vector"])

        Utility.insert_keyframe(self.blender_obj.data, "use_projector", frame)


    def get_energy(self, frame: int = None) -> float:
        """ Returns the energy of the light.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The energy at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.data.energy

    def get_color(self, frame: int = None) -> Color:
        """ Returns the RGB color of the light.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The color at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.data.color

    def get_distance(self, frame: int = None) -> float:
        """ Returns the falloff distance of the light (point where light is half the original intensity).

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The falloff distance at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.data.distance

    def get_type(self, frame: int = None) -> str:
        """ Returns the type of the light.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The type at the specified frame.
        """
        with KeyFrame(frame):
            return self.blender_obj.data.type
