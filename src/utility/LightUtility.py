from typing import Union

import bpy

from src.utility.Utility import Utility, KeyFrame
from mathutils import Vector, Euler, Color


class Light:
    def __init__(self, type: str = "POINT", name: str = "light"):
        """
        :param type: The initial type of light, can be one of [POINT, SUN, SPOT, AREA].
        :param name: The name of the new light
        """
        light_data = bpy.data.lights.new(name=name, type=type)
        self.light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        bpy.context.collection.objects.link(self.light_obj)

    def set_location(self, location: Union[list, Vector], frame: int = None):
        """ Sets the location of the light in 3D world coordinates.

        :param location: The location to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.light_obj.location = location
        Utility.insert_keyframe(self.light_obj, "location", frame)

    def set_rotation_euler(self, rotation_euler: Union[list, Euler], frame: int = None):
        """ Sets the rotation of the light in euler angles.

        :param rotation_euler: The euler angles to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.light_obj.rotation_euler = rotation_euler
        Utility.insert_keyframe(self.light_obj, "rotation_euler", frame)

    def set_energy(self, energy: float, frame: int = None):
        """ Sets the energy of the light.

        :param energy: The energy to set. If the type is SUN this value is interpreted as Watt per square meter, otherwise it is interpreted as Watt.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.light_obj.data.energy = energy
        Utility.insert_keyframe(self.light_obj.data, "energy", frame)

    def set_color(self, color: Union[list, Color], frame: int = None):
        """ Sets the color of the light.

        :param color: The rgb color to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.light_obj.data.color = color
        Utility.insert_keyframe(self.light_obj.data, "color", frame)

    def set_distance(self, distance: float, frame: int = None):
        """ Sets the falloff distance of the light = point where light is half the original intensity.

        :param distance: The falloff distance to set.
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.light_obj.data.distance = distance
        Utility.insert_keyframe(self.light_obj.data, "distance", frame)

    def set_type(self, type: str, frame: int = None):
        """ Sets the type of the light.

        :param type: The type to set, can be one of [POINT, SUN, SPOT, AREA].
        :param frame: The frame number which the value should be set to. If None is given, the current frame number is used.
        """
        self.light_obj.data.type = type
        Utility.insert_keyframe(self.light_obj.data, "type", frame)

    def get_location(self, frame: int = None) -> Vector:
        """ Returns the location of the light in 3D world coordinates.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The location at the specified frame.
        """
        with KeyFrame(frame):
            return self.light_obj.location

    def get_rotation(self, frame: int = None) -> Euler:
        """ Returns the rotation of the light in euler angles.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The rotation at the specified frame.
        """
        with KeyFrame(frame):
            return self.light_obj.rotation_euler

    def get_energy(self, frame: int = None) -> float:
        """ Returns the energy of the light.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The energy at the specified frame.
        """
        with KeyFrame(frame):
            return self.light_obj.data.energy

    def get_color(self, frame: int = None) -> Color:
        """ Returns the RGB color of the light.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The color at the specified frame.
        """
        with KeyFrame(frame):
            return self.light_obj.data.color

    def get_distance(self, frame: int = None) -> float:
        """ Returns the falloff distance of the light (point where light is half the original intensity).

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The falloff distance at the specified frame.
        """
        with KeyFrame(frame):
            return self.light_obj.data.distance

    def get_type(self, frame: int = None) -> str:
        """ Returns the type of the light.

        :param frame: The frame number at which the value should be returned. If None is given, the current frame number is used.
        :return: The type at the specified frame.
        """
        with KeyFrame(frame):
            return self.light_obj.data.type
