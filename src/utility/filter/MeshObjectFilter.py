from typing import Any

from src.utility.EntityUtility import Entity
from src.utility.MeshObjectUtility import MeshObject
from src.utility.StructUtility import Struct
from src.utility.filter.StructFilter import StructFilter


class MeshObjectFilter(StructFilter):

    @staticmethod
    def all_mesh_objects(structs: [Struct]) -> [MeshObject]:
        """ Returns all mesh objects from the given list.

        :param structs: A list of elements.
        :return: All mesh objects from the given list.
        """
        return filter(lambda x: isinstance(x, MeshObject), structs)
