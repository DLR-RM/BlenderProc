import warnings
from random import choice

import bpy
import numpy as np

import src.utility.BlenderUtility as BlenderUtility
from src.loader.LoaderInterface import LoaderInterface
from src.main.Module import Module
from src.provider.getter.Material import Material
from src.utility.Config import Config


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
              "name": "Solidify",
              "thickness": 0.001
            }
          }
        }

        Example 4: Add a displacement modifier with a newly generated texture.

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
            "cf_add_displace_modifier_with_texture": {
              "texture": 'VORONOI'
            }
          }
        }

        Example 5: Add a displacement modifier with a newly random generated texture with custom
                   texture, noise scale, modifier mid_level, modifier render_level and modifier strength. With
                   prior addition of a uv_map to all object without an uv map and adding of a Subdivision Surface
                   Modifier if the number of vertices of an object is less than 10000.

        {
          "module": "manipulators.EntityManipulator",
          "config": {
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "name": 'apple',
                "type": "MESH"
              }
            },
            "cf_add_uv_mapping":{
              "projection": "cylinder"
            },
            "cf_add_displace_modifier_with_texture": {
              "texture": {
                "provider": "sampler.Texture"
              },
              "min_vertices_for_subdiv": 10000,
              "mid_level": 0.5,
              "subdiv_level": {
                "provider": "sampler.Value",
                "type": "int",
                "min": 1,
                "max": 3
              },
              "strength": {
                "provider": "sampler.Value",
                "type": "float",
                "mode": "normal",
                "mean": 0.0,
                "std_dev": 0.7
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
        "index", "If set, after the conditions are applied only the entity with the specified index is returned. "
                 "Type: int."
        "random_samples", "If set, this Provider returns random_samples objects from the pool of selected ones. Define "
                          "index or random_samples property, only one is allowed at a time. Type: int. Default: False."

    **Custom functions**

    .. csv-table::
        :header: "Parameter", "Description"

        "cf_add_modifier", "Adds a modifier to the selected object. Type: dict."
        "cf_add_modifier/name", "Name of the modifier to add. Type: string. Available values: 'Solidify'."
        "cf_add_modifier/thickness", "'thickness' attribute of the 'Solidify' modifier. Type: float."
        "cf_set_shading", "Custom function to set the shading of the selected object."
                          "Type: str. Available: ["FLAT", "SMOOTH"]"
        "cf_add_displace_modifier_with_texture", "Adds a displace modifier with texture to an object. Type: dict."
        "cf_add_displace_modifier_with_texture/texture", "The structure is either a given or a random texture."
                                                           "Type: str. Default: []. Available:['CLOUDS',"
                                                           "'DISTORTED_NOISE', 'MAGIC', 'MARBLE', 'MUSGRAVE', 'NOISE',"
                                                           "'STUCCI', 'VORONOI', 'WOOD']"
        "cf_add_displace_modifier_with_texture/min_vertices_for_subdiv", "Checks if a subdivision is necessary. If"
                                                                           "the vertices of a object are less than"
                                                                           "'min_vertices_for_subdiv' a Subdivision"
                                                                           "modifier will be add to the object."
                                                                           "Type: int. Default: 10000."
        "cf_add_displace_modifier_with_texture/mid_level", "Texture value that gives no displacement."
                                                             "Parameter of displace modifier."
                                                             "Type: float. Default: 0.5"
        "cf_add_displace_modifier_with_texture/subdiv_level", "Numbers of Subdivisions to perform when"
                                                                "rendering. Parameter of Subdivision"
                                                                "modifier. Type: int. Default: 2"
        "cf_add_displace_modifier_with_texture/strength", "Amount to displace geometry. Parameter of displace"
                                                            "modifier. Type: float. Default: 0.1"
        "cf_add_uv_mapping", "Adds a uv map to an object if uv map is missing. Type: dict."
        "cf_add_uv_mapping/projection", "Name of the projection as str. Type: str. Default: []."
                                        "Available: ["cube", "cylinder", "smart", "sphere"]"
        "cf_randomize_materials", "Randomizes the materials for the selected objects with certain probability."
        "cf_randomize_materials/randomization_level", "Expected fraction of the selected objects for which the texture "
                                                      "should be randomized. Type: float. Range: [0, 1]. Default: 0.2."
        "cf_randomize_materials/materials_to_replace_with", "Material(s) to participate in randomization. Sampling "
                                                            "from the pool of elegible material (that comply with "
                                                            "conditions is performed in the Provider). Make sure you "
                                                            "use 'random_samples" config parameter of the Provider, if "
                                                            "multiple materials are returned, the first one will be "
                                                            "considered as a substitute during randomization. "
                                                            "Type: Provider. Default: random material."
        "cf_randomize_materials/obj_materials_cond_to_be_replaced", "A dict of materials and corresponding conditions "
                                                                    "making it possible to only replace materials with "
                                                                    "certain properties. These are similar to the "
                                                                    "conditions mentioned in the getter.Material. "
                                                                    "Type: dict. Default: {}."
    """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """
            Sets according values of defined attributes/custom properties or applies custom functions to the selected
            entities.
        """
        # separating defined part with the selector from ambiguous part with attribute names and their values to set
        set_params = {}
        sel_objs = {}
        for key in self.config.data.keys():
            if key != 'selector' and key != "mode":
                # if its not a selector -> to the set parameters dict
                set_params[key] = self.config.data[key]
            else:
                sel_objs[key] = self.config.data[key]
        # create Config objects
        params_conf = Config(set_params)
        sel_conf = Config(sel_objs)
        # invoke a Getter, get a list of entities to manipulate
        entities = sel_conf.get_list("selector")

        op_mode = self.config.get_string("mode", "once_for_each")

        if not entities:
            warnings.warn("Warning: No entities are selected. Check Providers conditions.")
            return
        else:
            print("Amount of objects to modify: {}.".format(len(entities)))

        # get raw value from the set parameters if it is to be sampled once for all selected entities
        if op_mode == "once_for_all":
            params = self._get_the_set_params(params_conf)

        for entity in entities:

            # get raw value from the set parameters if it is to be sampled anew for each selected entity
            if op_mode == "once_for_each":
                params = self._get_the_set_params(params_conf)

            for key, value in params.items():

                # used so we don't modify original key when having more than one entity
                key_copy = key

                # check if the key is a requested custom property
                requested_cp = False
                if key.startswith('cp_'):
                    requested_cp = True
                    key_copy = key[3:]
                requested_cf = False
                if key.startswith('cf_'):
                    requested_cf = True
                    key_copy = key[3:]

                # as an attribute of this value
                if hasattr(entity, key_copy) and not requested_cp:
                    setattr(entity, key_copy, value)
                # custom functions
                elif key_copy == "add_modifier" and requested_cf:
                    self._add_modifier(entity, value)
                elif key_copy == "set_shading" and requested_cf:
                    self._set_shading(entity, value)
                elif key_copy == "add_displace_modifier_with_texture" and requested_cf:
                    self._add_displace(entity, value)
                elif key_copy == "add_uv_mapping" and requested_cf:
                    self._add_uv_mapping(entity, value)
                elif key_copy == "randomize_materials" and requested_cf:
                    self._randomize_materials(entity, value)
                # if key had a cp_ prefix - treat it as a custom property
                # values will be overwritten for existing custom property,
                # but if the name is new then new custom property will be created
                elif requested_cp:
                    entity[key_copy] = value

        bpy.context.view_layer.update()

    def _get_the_set_params(self, params_conf):
        """ Extracts actual values to set from a Config object.

        :param params_conf: Object with all user-defined data. Type: Config.
        :return: Parameters to set as {name of the parameter: it's value} pairs. Type: dict.
        """
        params = {}
        for key in params_conf.data.keys():
            if key == "cf_add_modifier":
                modifier_config = Config(params_conf.get_raw_dict(key))
                # instruction about unpacking the data: key, corresponding Config method to extract the value,
                # it's default value and a postproc function
                instructions = {"name": (Config.get_string, None, str.upper),
                             "thickness": (Config.get_float, None, None)}
                # unpack
                result = self._unpack_params(modifier_config, instructions)
            elif key == "cf_set_shading":
                result = params_conf.get_string("cf_set_shading")
            elif key == "cf_add_displace_modifier_with_texture":
                displace_config = Config(params_conf.get_raw_dict(key))
                # instruction about unpacking the data: key, corresponding Config method to extract the value,
                # it's default value and a postproc function
                instructions = {"texture": (Config.get_raw_value, [], None),
                             "mid_level": (Config.get_float, 0.5, None),
                             "subdiv_level": (Config.get_int, 2, None),
                             "strength": (Config.get_float, 0.1, None),
                             "min_vertices_for_subdiv": (Config.get_int, 10000, None)}
                # unpack
                result = self._unpack_params(displace_config, instructions)
            elif key == "cf_add_uv_mapping":
                uv_config = Config(params_conf.get_raw_dict(key))
                # instruction about unpacking the data: key, corresponding Config method to extract the value,
                # it's default value and a postproc function
                instructions = {"projection": (Config.get_string, None, str.lower)}
                # unpack
                result = self._unpack_params(uv_config, instructions)
            elif key == "cf_randomize_materials":
                rand_config = Config(params_conf.get_raw_dict(key))
                # instruction about unpacking the data: key, corresponding Config method to extract the value,
                # it's default value and a postproc function
                instructions = {"randomization_level": (Config.get_float, 0.2, None),
                                "materials_to_replace_with": (Config.get_list,
                                                              [choice(BlenderUtility.get_all_materials())], None),
                                "obj_materials_cond_to_be_replaced": (Config.get_raw_dict, {}, None)}
                result = self._unpack_params(rand_config, instructions)
            else:
                result = params_conf.get_raw_value(key)

            params.update({key: result})

        return params

    def _add_modifier(self, entity, value):
        """ Adds modifier to a selected entity.

        :param entity: An entity to modify. Type: bpy.types.Object
        :param value: Configuration data. Type: dict.
        """
        if value["name"] == "SOLIDIFY":
            bpy.context.view_layer.objects.active = entity
            bpy.ops.object.modifier_add(type=value["name"])
            bpy.context.object.modifiers["Solidify"].thickness = value["thickness"]
        else:
            raise Exception("Unknown modifier: {}.".format(value["name"]))

    def _set_shading(self, entity, value):
        """ Switches shading mode of the selected entity.

        :param entity: An entity to modify. Type: bpy.types.Object
        :param value: Configuration data. Type: dict.
        """
        LoaderInterface.change_shading_mode([entity], value)

    def _add_displace(self, entity, value):
        """ Adds a displace modifier with texture to an object.

        :param entity: An object to modify. Type: bpy.types.Object.
        :param value: Configuration data. Type: dict.
        """
        bpy.context.view_layer.objects.active = entity
        if not len(entity.data.vertices) > value["min_vertices_for_subdiv"]:
            bpy.ops.object.modifier_add(type="SUBSURF")
            modifier = entity.modifiers[-1]
            modifier.render_levels = value["subdiv_level"]

        bpy.ops.object.modifier_add(type="DISPLACE")
        modifier = entity.modifiers[-1]
        modifier.texture = value["texture"]
        modifier.mid_level = value["mid_level"]
        modifier.strength = value["strength"]

    def _add_uv_mapping(self, entity, value):
        """ Adds a uv map to an object if uv map is missing.

        :param entity: An object to modify. Type: bpy.types.Object.
        :param value: Configuration data. Type: dict.
        """
        bpy.context.view_layer.objects.active = entity
        if hasattr(entity, "data") and entity.data is not None and \
                hasattr(entity.data, "uv_layers") and entity.data.uv_layers is not None:
            if not BlenderUtility.check_if_uv_coordinates_are_set(entity):
                bpy.ops.object.editmode_toggle()
                if value["projection"] == "cube":
                    bpy.ops.uv.cube_project()
                elif value["projection"] == "cylinder":
                    bpy.ops.uv.cylinder_project()
                elif value["projection"] == "smart":
                    bpy.ops.uv.smart_project()
                elif value["projection"] == "sphere":
                    bpy.ops.uv.sphere_project()
                else:
                    raise Exception("Unknown projection: '{}'. Please use 'cube', 'cylinder', 'smart' or 'sphere'."
                                    .format(value["projection"]))

                bpy.ops.object.editmode_toggle()

    def _randomize_materials(self, entity, value):
        """ Replaces each material of an entity with certain probability.

        :param entity: An object to modify. Type: bpy.types.Object.
        :param value: Configuration data. Type: dict.
        """
        if len(value["materials_to_replace_with"]) > 1:
            warnings.warn("getter.Material returned more than one substitute material, and random one of the returned "
                          "will be used. It means that multiple materials comply with conditions passed to the "
                          "Provider and 'random_samples' parameter is not enabled in the Provider (or multiple samples "
                          "are returned). Sampling should be performed on the level of the Provider (make sure to use "
                          "'random_samples': 1 as a config parameter for the getter.Material).")
            value["materials_to_replace_with"] = [choice(value["materials_to_replace_with"])]
        if hasattr(entity, 'material_slots'):
            for mat in entity.material_slots:
                use_mat = True
                if value["obj_materials_cond_to_be_replaced"]:
                    use_mat = len(Material.perform_and_condition_check(value["obj_materials_cond_to_be_replaced"], [],
                                                                       [mat.material])) == 1
                if use_mat:
                    if np.random.uniform(0, 1) <= value["randomization_level"]:
                        mat.material = value["materials_to_replace_with"][0]

    def _unpack_params(self, param_config, instructions):
        """ Unpacks the data from a config object following the instructions in the dict.

        :param instructions: Instruction for unpacking: keys, corresponding Config method to extract the value, default
        value, and a function to perform on the value after extraction. Type: dict.
        :param param_config: Structure that contains the unpacked data. Type: Config.
        :return: Unpacked data. Type: dict.
        """
        # check what was defined by the user
        for defined_key in param_config.data:
            if defined_key not in instructions:
                warnings.warn("Warning: key '{}' is not expected. Check spelling/docu for this cf.".format(defined_key))

        result = {}
        # for each key and a corresponding instructions
        for key, (config_fct, default_val, result_fct) in instructions.items():
            # check if whatever was defined as a desired Config method is callable
            if callable(config_fct):
                # extract the value of the requested type
                val = config_fct(param_config, key, default_val)
                # if a function to be applied to this value after extraction is defined - use it
                if result_fct:
                    val = result_fct(val)

                result.update({key: val})

        return result
