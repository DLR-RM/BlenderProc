import bpy

from src.main.Module import Module
from src.utility.Config import Config
from src.loader.Loader import Loader
import src.utility.BlenderUtility as BlenderUtility

class EntityManipulator(Module):
    """ Performs manipulation on selected entities of different Blender built-in types, e.g. Mesh objects, Camera
        objects, Light objects, etc.

        Example 1: For all 'MESH' type objects with a name matching a 'Cube.*' pattern set rotation Euler vector and set
                   custom property `physics`.

        {
          "module": "manipulators.EntityManipulator",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": 'Cube.*',
                "type": "MESH"
              }
            },
            "rotation_euler": [1, 1, 0],
            "cp_physics": True
          }
        }

        Example 2: Set a shared (sampled once and set for all selected objects) location for all 'MESH' type objects
                   with a name matching a 'Cube.*' pattern.

        {
          "module": "manipulators.EntityManipulator",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": 'Cube.*',
                "type": "MESH"
              }
            },
            "mode": "once_for_all",
            "location": {
              "provider": "sampler.Uniform3d",
              "max":[1, 2, 3],
              "min":[0, 1, 2]
            }
          }
        }

        Example 3: Set a unique (sampled once for each selected object) location and apply a 'Solidify' object modifier
                   with custom 'thickness' attribute value to all 'MESH' type objects with a name matching a 'Cube.*'
                   pattern.

        {
          "module": "manipulators.EntityManipulator",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": 'Cube.*',
                "type": "MESH"
              }
            },
            "mode": "once_for_each",    # can be omitted, `once_for_each` is a default value of `mode` parameter
            "location": {
              "provider": "sampler.Uniform3d",
              "max":[1, 2, 3],
              "min":[0, 1, 2]
            },
            "cf_add_modifier": {
              "provider": "getter.Content",
              "content": {
                "name": "Solidify",
                "thickness": 0.001
            }
          }
        }

        Example 4: Add a specific texture to the displacement modifier of a given object.

         {
          "module": "manipulators.EntityManipulator",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": 'Cube.*',
                "type": "MESH"
              }
            },
            "cf_add_displace_modifier_with_structure": {
             "provider": "getter.Content",
              "content": {
                "texture": 'VORONOI'
              }
            }
          }
        }

        Example 5: Add a random generated texture to the displacement modifier of a given object_type with custom
                   texture, noice scale, modifier mid_level, modifier render_level and modifier strength. With
                   previous adding of uv_map to all object without an uv map and adding a Subdivision Surface Modifier
                   if the number of vertices of an object is less than 10000.

        {
          "module": "manipulators.EntityManipulator",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "cp_type": 'apple'
              }
            },
            "cf_add_uv_mapping":{
              "provider": "getter.Content",
              "content": {
                "projection": "cylinder"
              }
            },
            "cf_add_displace_modifier_with_structure": {
              "provider": "getter.Content",
              "content": {
                  "texture": {
                    "provider": "sampler.Texture",
                    "noice_scale": 40"
                  },
                  "min_vertices": 10000,
                  "modifier_mid_level": 0.5,
                  "modifier_render_level": {
                    "provider": "sampler.Value",
                    "type": "int",
                    "min": 1,
                    "max": 3
                  },
                  "modifier_strength": {
                    "provider": "sampler.Value",
                    "type": "dist",
                    "mean": 0.0,
                    "std_dev": 0.7
                  }
              }

            }
          }
        }


    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "selector", "Objects to become subjects of manipulation. Type: Provider."
        "mode", "Mode of operation. Type: string. Default: "once_for_each". Available: 'once_for_each' (if samplers "
                "are called, new sampled value is set to each selected entity), 'once_for_all' (if samplers are "
                "called, value is sampled once and set to all selected entities)."

    **Values to set**:

    .. csv-table::
        :header: "Parameter", "Description"

        "key", "Name of the attribute/custom property to change or a name of a custom function to perform on entities. "
               "Type: string. "
               "In order to specify, what exactly one wants to modify (e.g. attribute, custom property, etc.): "
               "For attribute: key of the pair must be a valid attribute name of the selected object. "
               "For custom property: key of the pair must start with `cp_` prefix. "
               "For calling custom function: key of the pair must start with `cf_` prefix. See table below for "
               "supported custom function names."
        "value", "Value of the attribute/custom prop. to set or input value(s) for a custom function. Type: string, "
                 "int, bool or float, list/Vector."

    **Custom functions**

    .. csv-table::
        :header: "Parameter", "Description"

        "cf_add_modifier", "Adds a modifier to the selected object. Pass configuration parameters via calling a "
                           "getter.Content Provider. Type: Provider."
        "cf_add_modifier/name", "Name of the modifier to add. Type: string. Available values: 'Solidify'."
        "cf_add_modifier/thickness", "'thickness' attribute of the 'Solidify' modifier. Type: float."
        "cf_set_shading", "Custom function to set the shading of the selected object."
                          "Type: str. Available: ["FLAT", "SMOOTH"]"
        "cf_add_displace_modifier_with_structure", "Adds a displace modifier with structure to an object."
                                                   "getter.Content Provider. Type: Provider."
        "cf_add_displace_modifier_with_structure/texture", "The structure is either a given or a random texture."
                                                           "Available textures are ["CLOUDS", "DISTORTED_NOISE","
                                                           ""MAGIC", "MARBLE", "MUSGRAVE", "NOICE", "STUCCI","VORONOI","
                                                           ""WOOD"]. Type: str. Default: []"
        "cf_add_displace_modifier_with_structure/min_vertices", "Checks if a subdivision is necessary. If the vertices"
                                                                "of a object are less than 'min_vertices' a"
                                                                "Subdivision modifier will be add to the object."
                                                                "Type: int. Default: 10000."
        "cf_add_displace_modifier_with_structure/modifier_mid_level", "Sets the mid level of the displace modifier."
                                                                      "Type: float. Default: 0.5"
        "cf_add_displace_modifier_with_structure/modifier_render_level", "Sets the render level of the displace"
                                                                         "modifier. Type: int. Default: 2"
        "cf_add_displace_modifier_with_structure/modifier_strength", "Sets the strength of the displace modifier."
                                                                     "Type: float. Default: 0.1"
        "cf_add_uv_mapping", "Adds a uv map to an object if uv map is missing. getter.Content Provider. Type: Provider"
        "cf_add_uv_mapping/projection", "Name of the projection as str. Type: str. Default: []."
                                        "Available: ["cube", "cylinder", "smart", "sphere"]"
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Sets according values of defined attributes/custom properties or applies custom functions to the selected
            entities.
            1. Select objects.
            2. For each parameter to modify, set it's value to all selected objects.
        """
        # separating defined part with the selector from ambiguous part with attribute names and their values to set
        set_params = {}
        sel_objs = {}
        for key in self.config.data.keys():
            # if its not a selector -> to the set parameters dict
            if key != 'selector':
                set_params[key] = self.config.data[key]
            else:
                sel_objs[key] = self.config.data[key]
        # create Config objects
        params_conf = Config(set_params)
        sel_conf = Config(sel_objs)
        # invoke a Getter, get a list of entities to manipulate
        entities = sel_conf.get_list("selector")

        op_mode = self.config.get_string("mode", "once_for_each")
        if len(entities) == 0:
            raise RuntimeError("No objects are returned by Provider. Check defined conditions.")
        else:
            print("Amount of objects to modify: {}.".format(len(entities)))

        for key in params_conf.data.keys():
            # get raw value from the set parameters if it is to be sampled once for all selected entities
            if op_mode == "once_for_all":
                result = params_conf.get_raw_value(key)

            for entity in entities:
                if op_mode == "once_for_each":
                    # get raw value from the set parameters if it is to be sampled anew for each selected entity
                    result = params_conf.get_raw_value(key)

                # used so we don't modify original key when having more than one entity
                key_copy = key

                # check if the key is a requested custom property
                demanded_custom_property = False
                if key.startswith('cp_'):
                    demanded_custom_property = True
                    key_copy = key[3:]
                demanded_custom_function = False
                if key.startswith('cf_'):
                    demanded_custom_function = True
                    key_copy = key[3:]

                # if an attribute with such name exists for this entity
                if hasattr(entity, key_copy) and not demanded_custom_property:
                    # set the value
                    setattr(entity, key_copy, result)
                # if key had a cf_ prefix - treat it as a custom function.
                elif demanded_custom_function:
                    self._apply_function(entity, key_copy, result)
                # if key had a cp_ prefix - treat it as a custom property. Values will be overwritten for existing
                # custom property, but if the name is new then new custom property will be created
                elif demanded_custom_property:
                    entity[key_copy] = result
        # update all entities matrices
        bpy.context.view_layer.update()

    def _apply_function(self, entity, key, result):
        """ Applies a custom function to the selected entity.

        :param entity: Entity to be modified via the application of the custom function. Type: bpy.types.Object.
        :param key: Name of the custom function. Type: string.
        :param result: Configuration parameters of the custom function. Type: dict.
        """
        if key == "add_modifier":
            result = Config(result)
            name = result.get_string("name")  # the name of the modifier
            if name.upper() == "SOLIDIFY":
                thickness = result.get_float("thickness")
                bpy.context.view_layer.objects.active = entity
                bpy.ops.object.modifier_add(type=name.upper())
                bpy.context.object.modifiers["Solidify"].thickness = thickness
            else:
                raise Exception("Unknown modifier name: {}.".format(name))

        elif key == "set_shading":
            result = Config(result)
            mode = result.get_string("cf_set_shaing")
            Loader.change_shading_mode([entity], mode)

        elif key == "add_displace_modifier_with_structure":
            result = Config(result)
            tex = result.get_raw_value("texture", [])
            if tex is not None:

                if not isinstance(tex, bpy.types.Texture):
                    raise Exception("The given texture {} is not existing in blender".format(tex.name))

                modifier_mid_level = result.get_float("modifier_mid_level", 0.5)
                modifier_render_level = result.get_int("modifier_render_level", 2)
                modifier_strength = result.get_float("modifier_strength", 0.1)
                min_vertices = result.get_int("min_vertices", 10000)

                bpy.context.view_layer.objects.active = entity
                if not len(entity.data.vertices) > min_vertices:
                    bpy.ops.object.modifier_add(type="Subsurf".upper())
                    modifier = entity.modifiers[-1]
                    modifier.render_levels = modifier_render_level

                bpy.ops.object.modifier_add(type="Displace".upper()) # does not return anything
                modifier = entity.modifiers[-1]
                modifier.texture = tex
                modifier.mid_level = modifier_mid_level
                modifier.strength = modifier_strength
            else:
                raise Exception("No texture given for add_displace_modifier_with_structure")

        elif key == "add_uv_layer":
            result = Config(result)
            projection = result.get_string("projection").lower()

            bpy.context.view_layer.objects.active = entity
            if hasattr(entity, "data") and entity.data is not None and \
                    hasattr(entity.data, "uv_layers") and entity.data.uv_layers is not None:
                if not BlenderUtility.check_if_uv_coordinates_are_set(entity):
                    bpy.ops.object.editmode_toggle()
                    if projection == "cube":
                        bpy.ops.uv.cube_project()
                    elif projection == "cylinder":
                        bpy.ops.uv.cylinder_project()
                    elif projection == "smart":
                        bpy.ops.uv.smart_project()
                    elif projection == "sphere":
                        bpy.ops.uv.sphere_project()
                    else:
                        raise Exception("Projection {} does not exist! Please use cube, cylinder, smart or sphere"
                                        .format(projection))

                    bpy.ops.object.editmode_toggle()
        else:
            raise Exception("Unknown custom function name: {}.".format(key))
