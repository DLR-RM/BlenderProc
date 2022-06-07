from typing import Union
import numpy as np
from mathutils import Vector, Euler, Color, Matrix, Quaternion

import bpy

from blenderproc.python.types.EntityUtility import Entity


class Inertial(Entity):
    def __init__(self, bpy_object: bpy.types.Object):
        super().__init__(bpy_object=bpy_object)

        object.__setattr__(self, "inertia", None)
        object.__setattr__(self, "mass", None)
        object.__setattr__(self, "origin", None)

    def set_inertia(self, inertia: np.ndarray):
        """ Sets inertia value.

        :param inertia: 3x3 symmetric rotational inertia matrix.
        """
        assert inertia.shape == (3, 3)
        object.__setattr__(self, "inertia", inertia)

    def get_inertia(self) -> np.ndarray:
        """ Returns the inertia.

        :return: The inertia matrix.
        """
        return self.inertia

    def set_mass(self, mass: float):
        """ Sets the mass.

        :param mass: Mass of the link in kilograms.
        """
        object.__setattr__(self, "mass", mass)

    def get_mass(self) -> float:
        """ Returns the mass of the link.

        :return: The mass.
        """
        return self.mass

    def set_origin(self, origin: Union[np.ndarray, Matrix]):
        """ Sets the origin and the world matrix of the inertia.

        :param origin: 4x4 matrix of the inertials relative to the link frame.
        """
        object.__setattr__(self, "origin", Matrix(origin))
        self.blender_obj.matrix_world = Matrix(origin)

    def get_origin(self) -> Matrix:
        """ Returns the origin of the inertia.

        :return: The pose relative to the link frame.
        """
        return self.origin

    def hide(self, hide_object: bool = True):
        """ Sets the visibility of the object.

        :param hide_object: Determines whether the object should be hidden in rendering.
        """
        self.blender_obj.hide_render = hide_object
