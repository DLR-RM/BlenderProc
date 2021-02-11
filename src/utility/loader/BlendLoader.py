import os
import re
from typing import List

import bpy

from src.utility.MeshUtility import Mesh
from src.utility.Utility import Utility


class BlendLoader:
    known_datablock_names = {"/Camera": "cameras",
                              "/Collection": "collections",
                              "/Image": "images",
                              "/Light": "lights",
                              "/Material": "materials",
                              "/Mesh": "meshes",
                              "/Object": "objects",
                              "/Texture": "textures"}

    @staticmethod
    def load(path: str, load_from: str, entities: str = None) -> List[Mesh]:
        """
        Loads entities (everything that can be stored in a .blend file's folders, see Blender's documentation for
        bpy.types.ID for more info) that match a name pattern from a specified .blend file's section/datablock.

        :param path: Path to a .blend file.
        :param load_from: Name of the datablock/folder inside .blend file. Always start with '/'. See known_datablock_names for
                          supported folder names/type IDs.
        :param entities: Regular expression representing a name pattern of entities' (everything that can be stored in a .blend
                         file's folders, see Blender's documentation for bpy.types.ID for more info) names.
        :return: The list of loaded mesh objects.
        """
        # get a path to a .blend file
        path = Utility.resolve_path(path)

        previously_loaded_objects = set(bpy.context.scene.objects)

        with bpy.data.libraries.load(path) as (data_from, data_to):
            # check if defined ID is supported
            if load_from in BlendLoader.known_datablock_names.keys():
                # if some regex was specified, get corresponding matching entity's names
                if entities is not None:
                    entities_to_load = [item for item in getattr(data_from, BlendLoader.known_datablock_names[load_from])
                                        if re.fullmatch(entities, item) is not None]
                # get all entity's names if not
                else:
                    entities_to_load = getattr(data_from, BlendLoader.known_datablock_names[load_from])
                # load entities
                for entity_to_load in entities_to_load:
                    bpy.ops.wm.append(filepath=os.path.join(path, load_from, entity_to_load),
                                      filename=entity_to_load,
                                      directory=os.path.join(path + load_from))
            else:
                raise Exception("Unsupported datablock/folder name: " + load_from +
                                "\nSupported names: " + str(BlendLoader.known_datablock_names.keys()) +
                                "\nIf your ID exists, but not supported, please append a new pair of "
                                "{type ID(folder name): parameter name} to the 'known_datablock_names' dict. Use this "
                                "for finding your parameter name: " + str(dir(data_from)))
        newly_loaded_objects = list(set(bpy.context.scene.objects) - previously_loaded_objects)
        return Mesh.convert_to_meshes(newly_loaded_objects)
