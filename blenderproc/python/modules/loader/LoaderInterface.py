from blenderproc.python.modules.main.Module import Module
from blenderproc.python.types.EntityUtility import Entity
from blenderproc.python.types.MeshObjectUtility import MeshObject
from blenderproc.python.types.StructUtility import Struct
from blenderproc.python.object.ObjectMerging import merge_objects

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

    def _set_properties(self, objects: [Entity]):
        """ Sets all custom properties of all given objects according to the configuration.

        Also runs all custom property functions.

        :param objects: A list of objects which should receive the custom properties.
        """

        should_merge_objects = self.config.get_bool("cf_merge_objects", False)
        if should_merge_objects:
            merged_object_name = self.config.get_string("cf_merged_object_name", "merged_object")
            parent_object = merge_objects(objects=objects, merged_object_name=merged_object_name)
            objects.append(parent_object)

        properties = self.config.get_raw_dict("add_properties", {})
        material_properties = self.config.get_raw_dict("add_material_properties", {})

        for obj in objects:
            for key, value in properties.items():
                if key.startswith("cp_"):
                    key = key[3:]
                    if isinstance(obj, Struct):
                        obj.set_cp(key, value)
                    else:
                        obj[key] = value
                else:
                    raise RuntimeError(
                        "Loader modules support setting only custom properties. Use 'cp_' prefix for keys. "
                        "Use manipulators.Entity for setting object's attribute values.")
            if material_properties and isinstance(obj, MeshObject):
                for material in obj.get_materials():
                    if material is None:
                        continue
                    for key, value in material_properties.items():
                        if key.startswith("cp_"):
                            key = key[3:]
                            material.set_cp(key, value)
                        else:
                            raise RuntimeError("Loader modules support setting only custom properties. "
                                               "Use 'cp_' prefix for keys.")

            # only meshes have polygons/faces
            if isinstance(obj, MeshObject):
                if self.config.has_param("cf_set_shading"):
                    mode = self.config.get_string("cf_set_shading")
                    angle_value = self.config.get_float("cf_shading_auto_smooth_angle_in_deg", 30)
                    obj.set_shading_mode(mode, angle_value)

                if self.config.get_bool("cf_apply_transformation", False):
                    obj.persist_transformation_into_mesh()
