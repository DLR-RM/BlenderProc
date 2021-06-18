from typing import Any

from src.utility.EntityUtility import Entity
from src.utility.MeshObjectUtility import MeshObject
from src.utility.StructUtility import Struct
from src.utility.filter.StructFilter import StructFilter


class MeshObjectFilter(StructFilter):

    def all_mesh_objects(self, structs: [Struct]) -> [MeshObject]:
        return filter(lambda x: isinstance(x, MeshObject), structs)
