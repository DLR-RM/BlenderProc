import bpy

from src.main.Module import Module
from src.utility.EntityUtility import Entity
from src.utility.MeshObjectUtility import MeshObject
from src.utility.object.ObjectMerging import ObjectMerging
from typing import Union
import numpy as np

class LoaderInterface(Module):
    """
    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - add_properties
          - Custom properties to set for loaded objects. Use `cp_` prefix for keys.
          - dict
        * - add_material_properties
          - Custom properties to set for the materials of loaded objects. Use `cp_` prefix for keys. This only works
            for materials which are used. Additional materials, which are loaded for example via a .blend file, are not
            affected by this.
          - dict
        * - cf_set_shading
          - Custom function to set the shading of the selected object. Default: 'FLAT'.
            Available: ['FLAT', 'SMOOTH', 'AUTO'].
          - str
        * - cf_shading_auto_smooth_angle_in_deg
          - Angle in degrees at which flat shading is activated in `AUTO` mode. Default: 30.
          - float
        * - cf_apply_transformation
          - Loaded objects, sometimes contain transformations, these can be applied to the mesh, so that setting a
            new location, has the expected behavior. Else the prior location, will be replaced. Default: False.
          - bool
        * - cf_merge_objects
          - Merges a list of objects by creating an empty object and assinging it as parent to every object which does
            not already have a parent. Returns the list of objects including the newly created empty parent.
          - list
        * - cf_merged_object_name
          - Name of the empty parent object. Default: `merged_object`.
          - str
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def _set_properties(self, objects: Union[bpy.types.Object, Entity]):
        """ Sets all custom properties of all given objects according to the configuration.

        Also runs all custom property functions.

        :param objects: A list of objects which should receive the custom properties.
        """

        properties = self.config.get_raw_dict("add_properties", {})
        material_properties = self.config.get_raw_dict("add_material_properties", {})

        for obj in objects:
            for key, value in properties.items():
                if key.startswith("cp_"):
                    key = key[3:]
                    if isinstance(obj, Entity):
                        obj.set_cp(key, value)
                    else:
                        obj[key] = value
                else:
                    raise RuntimeError(
                        "Loader modules support setting only custom properties. Use 'cp_' prefix for keys. "
                        "Use manipulators.Entity for setting object's attribute values.")
            if material_properties and hasattr(obj, "material_slots"):
                for material in (obj.get_materials() if isinstance(obj, MeshObject) else obj.data.materials):
                    if material is None:
                        continue
                    for key, value in material_properties.items():
                        if key.startswith("cp_"):
                            key = key[3:]
                            material[key] = value
                        else:
                            raise RuntimeError("Loader modules support setting only custom properties. "
                                               "Use 'cp_' prefix for keys.")

            # only meshes have polygons/faces
            if hasattr(obj, 'type') and obj.type == 'MESH':
                if self.config.has_param("cf_set_shading"):
                    mode = self.config.get_string("cf_set_shading")
                    angle_value = self.config.get_float("cf_shading_auto_smooth_angle_in_deg", 30)
                    LoaderInterface.change_shading_mode([obj], mode, angle_value)

        apply_transformation = self.config.get_bool("cf_apply_transformation", False)
        if apply_transformation:
            LoaderInterface.apply_transformation_to_objects(objects)

        merge_objects = self.config.get_bool("cf_merge_objects", False)
        if merge_objects:
            merged_object_name = self.config.get_string("cf_merged_object_name", "merged_object")
            objects = ObjectMerging.merge_object_list(objects=objects, merged_object_name=merged_object_name)

    @staticmethod
    def apply_transformation_to_objects(objects: [bpy.types.Object]):
        """
        Apply the current transformation of the object, which are saved in the location, scale or rotation attributes
        to the mesh and sets them to their init values.

        :param objects: List of objects, which should be changed
        """
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            # only bpy.types.Object (subclass of bpy.types.ID) have transformation
            if isinstance(obj, bpy.types.Object):
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                obj.select_set(False)
        bpy.ops.object.select_all(action='DESELECT')

    @staticmethod
    def change_shading_mode(objects: [bpy.types.Object], mode: str, angle_value: float):
        """
        Changes the shading mode of all objects to either flat or smooth. All surfaces of that object are changed.

        :param objects: A list of objects which should receive the custom properties. Type: [bpy.types.Object]
        :param mode: Desired mode of the shading. Available: ["FLAT", "SMOOTH", "AUTO"]. Type: str
        :param angle_value: Angle in degrees at which flat shading is activated in `AUTO` mode. Type: float
        """
        if mode.lower() == "flat":
            is_smooth = False
            for obj in objects:
                obj.data.use_auto_smooth = False
        elif mode.lower() == "smooth":
            is_smooth = True
            for obj in objects:
                obj.data.use_auto_smooth = False
        elif mode.lower() == "auto":
            is_smooth = True
            for obj in objects:
                obj.data.use_auto_smooth = True
                obj.data.auto_smooth_angle = np.deg2rad(angle_value)
        else:
            raise Exception("This shading mode is unknown: {}".format(mode))

        for obj in objects:
            if isinstance(obj, MeshObject):
                obj.set_shading_mode(is_smooth)
            else:
                for face in obj.data.polygons:
                    face.use_smooth = is_smooth
