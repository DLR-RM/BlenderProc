import os
import random
import warnings
from typing import Any

import bpy

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.material import MaterialLoaderUtility
from blenderproc.python.material import Dust


class MaterialManipulator(Module):
    """
    Performs manipulation os selected materials.

    Example 1: Link image texture output of the 'Material.001' material to displacement input of the shader with a
               strength factor of 1.5.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config": {
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": "Material.001"
              }
            },
            "cf_color_link_to_displacement": 1.5
          }
        }

    Example 2: Set base color of all materials matching the name pattern to white.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config": {
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": ".*material.*"
              }
            },
            "cf_set_base_color": [1, 1, 1, 1]
          }
        }

    Example 3: For all materials matching the name pattern switch to the Emission shader with emitted light of red
    color of energy 15.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config": {
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": ".*material.*"
              }
            },
            "cf_switch_to_emission_shader": {
              "color": [1, 0, 0, 1],
              "strength": 15
            }
          }
        }

    Example 4: Add a layer of dust to all materials. By using a random generated dust texture. The strength here
    determines how thick the dust layer is. The texture scale determines the size of the dust flakes. At one it gets
    the same as the normal texture on the object. Be aware that each object needs a UV map so that the dust flakes
    are properly displayed.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config":{
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": ".*",
                "use_nodes": True
              }
            },
            "cf_add_dust": {
              "strength": 0.8,
              "texture_scale": 0.05
            }
          }
        }

    Example 5: Add a layer of dust to all materials. In this example the focus is on loading a texture with the
    TextureLoader and using it with the MaterialManipulator.

    .. code-block:: yaml

        {
          "module": "loader.TextureLoader",
          "config": {
            "path": "<args:0>",
            "add_properties": {
              "cp_dust_texture": True
            }
          }
        },
        {
          "module": "manipulators.MaterialManipulator",
          "config":{
            "selector": {
              "provider": "getter.Material",
              "conditions": {
                "name": ".*",
                "use_nodes": True
              }
            },
            "cf_add_dust": {
              "strength": 0.8,
              "used_dust_texture": {
                "provider": "getter.Texture",
                "conditions": {
                  "cp_dust_texture": True
                }
              },
              "texture_scale": 0.05
            }
          }
        }

    Example 6: Adds a texture as an overlay over all materials, which are currently used. First the texture is loaded,
    via the `TextureLoader` and then it is used inside of the `"cf_infuse_texture"`

    .. code-block:: yaml

        {
          "module": "loader.TextureLoader",
          "config":{
            "path": "<args:3>",
            "add_properties": {
              "cp_dust_texture": True
            }
          }
        },
        {
          "module": "manipulators.MaterialManipulator",
          "config": {
            "selector": {
              "provider": "getter.Material",
              "conditions": {
               "cf_use_materials_of_objects": {
                 "provider": "getter.Entity",
                 "conditions": {
                   "type": "MESH"
                 }
               },
              }
            },
            "cf_infuse_texture": {
              "mode": "mix",
              "texture_scale": 1.0,
              "used_texture": {
                "provider": "getter.Texture",
                "conditions": {
                  "cp_dust_texture": True
                }
              }
            }
          }
        }

    Example 7: Combines two materials, this mixes all currently used materials, with all cc materials.

    .. code-block:: yaml

        {
          "module": "manipulators.MaterialManipulator",
          "config": {
           "selector": {
             "provider": "getter.Material",
             "conditions": {
              "cf_use_materials_of_objects": {
                "provider": "getter.Entity",
                "conditions": {
                  "type": "MESH"
                }
              },
             }
           },
           "cf_infuse_material": {
            "mode": "mix",
            "used_material": {
              "provider": "getter.Material",
              "check_empty": True,
              "conditions": {
                "cp_is_cc_texture": True
              }
            }
           }
          }
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - selector
          - Materials to become subjects of manipulation.
          - Provider
        * - mode
          - Mode of operation. Default: "once_for_each". Available: 'once_for_each' (if samplers are called, new sampled 
            value is set to each selected material), 'once_for_all' (sampling once for all of the selected materials).
          - string

    **Values to set**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - key
          - Name of the attribute to change or a name of a custom function to perform on materials. " In order to
            specify, what exactly one wants to modify (e.g. attribute, custom property, etc.): For attribute: key of
            the pair must be a valid attribute name of the selected material. For calling custom function: key of
            the pair must start with `cf_` prefix. See table below for supported custom function names.
          - string
        * - value
          - Value of the attribute/custom prop. to set or input value(s) for a custom function.
          - string, list/Vector, int, bool or float

    **Available custom functions**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cf_color_link_to_displacement
          - Factor that determines the strength of the displacement via linking the output of the texture image to
            the displacement
          - float
        * - cf_change_to_vertex_color
          - The name of the vertex color layer, used for changing the material to a vertex coloring mode. The object
            is still able to reflect light and influence the light around it
          - string
        * - change_to_vertex_color_no_shading
          - The name of the vertex color layer, used for changing the material to a vertex coloring mode. For this
            no shading is used.
          - string
        * - cf_textures
          - Texture data as {texture_type (type of the image/map, i.e. color, roughness, reflection, etc.):
            texture_path} pairs. Texture_type should be equal to the Shader input name in order to be assigned to a
            ShaderTexImage node that will be linked to this input. Label represents to which shader input this node
            is connected. 
          - dict
        * - cf_textures/texture_path
          - Path to a texture image.
          - string
        * - cf_switch_to_emission_shader
          - Adds the Emission shader to the target material, sets it's 'color' and 'strength' values, connects it to
            the Material Output node. 
          - dict
        * - cf_switch_to_emission_shader/color
          - [R, G, B, A] vector representing the color of the emitted light. 
          - mathutils.Vector
        * - cf_switch_to_emission_shader/strength
          - Strength of the emitted light. Must be >0.
          - float
        * - cf_add_dust
          - Adds a layer of dust on all target materials. Dust is always presented on every surface facing upwards
            in Z-direction.
          - dict
        * - cf_add_dust/strength
          - This determines the strength of the dust, 0 means no dust 1.0 means full dust. Values above 1.0 are
            possible, but create a thick film out of dust, which hides the material completely.
          - float
        * - cf_add_dust/used_dust_texture
          - If a specific dust texture should be used, this can be specified. Use a getter.Texture to return a loaded
            texture. If this is empty a random noise texture is generated.
          - getter.Texture
        * - cf_add_dust/texture_scale
          - This scale is used to scale down the used noise texture (even for the case where a random noise texture
            is used). Default: 0.1.
          - float
        * - cf_infuse_texture
          - With this custom function it is possible to overlay materials with a certain texture. This only works
            if there is one principled BSDF shader in this material, it will be used as a reference point.
          - dict
        * - cf_infuse_texture/mode
          - The mode determines how the texture is used. There are three options: "overlay" in which the selected
            texture is overlayed over a preexisting one. If there is none, nothing happens. The second option: "mix"
            is similar to overlay, just that the textures are mixed there. The last option: "set" replaces any existing
            texture and is even added if there was none before.
            Default: "overlay". Available: ["overlay", "mix", "set"].
          - str
        * - cf_infuse_texture/used_texture
          - A getter.Texture can be used here to select the texture, which should be infused in the material.
          - getter.Texture
        * - cf_infuse_texture/connection
          - By default the "Base Color" input of the principled shader will be used. This can be changed to any valid
            input of a principled shader. Default: "Base Color". For available check the blender documentation.
          - str
        * - cf_infuse_texture/strength
          - The strength determines how much the newly generated texture is going to be used. Default: 0.5.
          - float
        * - cf_infuse_texture/texture_scale
          - The used texture can be scaled down or up by a factor, to make it match the preexisting UV mapping. Make
            sure that the object has a UV mapping beforehand. Default: 0.05.
          - float
        * - cf_infuse_texture/invert_texture
          - It might be sometimes useful to invert the input texture, this can be done by setting this to True.
            Default: False.
          - bool
        * - cf_infuse_material
          - This can be used to fuse two materials together, this is applied to the selected materials. One can select
            inside of this the materials which will be copied inside of the other materials. Be aware this affects more
            than just the color it will also affect the displacement and the volume of the material.
          - dict
        * - cf_infuse_material/used_material
          - This selector (getter.Material) is used to select the materials, which will be copied into the materials
            selected by the "selector".
          - getter.Material
        * - cf_infuse_material/mode
          - The mode determines how the two materials are mixed. There are two options "mix" in which the
            preexisting material is mixed with the selected one in "used_material" or "add" in which they are just
            added on top of each other. Default: "mix". Available: ["mix", "add"]
          - str
        * - cf_infuse_material/mix_strength
          - In the "mix" mode a strength can be set to determine how much of each material is going to be used.
            A strength of 1.0 means that the new material is going to be used completely. Default: 0.5.
          - float
        * - cf_set_*
          - Sets value to the * (suffix) input of the Principled BSDF shader. Replace * with all lower-case name of
            the input (use '_' if those are represented by multiple nodes, e.g. 'Base Color' -> 'base_color'). Also
            deletes any links to this shader's input point.
          - list/Vector, int or float
        * - cf_add_*
          - Adds value to the * (suffix) input of the Principled BSDF shader. Replace * with all lower-case name of
            the input (use '_' if those are represented by multiple nodes, e.g. 'Base Color' -> 'base_color'). Also
            deletes any links to this shader's input point. The values are not clipped in the end.
          - list/Vector, int or float
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Sets according values of defined attributes or applies custom functions to the selected materials.
            1. Select materials.
            2. For each parameter to modify, set it's value to all selected objects.
        """
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
        materials = sel_conf.get_list("selector")
        materials = MaterialLoaderUtility.convert_to_materials(materials)

        op_mode = self.config.get_string("mode", "once_for_each")

        if not materials:
            warnings.warn("Warning: No materials selected inside of the MaterialManipulator")
            return

        if op_mode == "once_for_all":
            # get values to set if they are to be set/sampled once for all selected materials
            params = self._get_the_set_params(params_conf)

        for material in materials:
            if not material.blender_obj.use_nodes:
                raise Exception("This material does not use nodes -> not supported here.")

            if op_mode == "once_for_each":
                # get values to set if they are to be set/sampled anew for each selected entity
                params = self._get_the_set_params(params_conf)

            for key, value in params.items():

                # used so we don't modify original key when having more than one material
                key_copy = key

                requested_cf = False
                if key.startswith('cf_'):
                    requested_cf = True
                    key_copy = key[3:]

                # if an attribute with such name exists for this entity
                if key_copy == "color_link_to_displacement" and requested_cf:
                    MaterialManipulator._link_color_to_displacement_for_mat(material, value)
                elif key_copy == "change_to_vertex_color" and requested_cf:
                    MaterialManipulator._map_vertex_color(material, value, active_shading=True)
                elif key_copy == "change_to_vertex_color_no_shading" and requested_cf:
                    MaterialManipulator._map_vertex_color(material, value, active_shading=False)
                elif key_copy == "textures" and requested_cf:
                    loaded_textures = self._load_textures(value)
                    self._set_textures(loaded_textures, material)
                elif key_copy == "switch_to_emission_shader" and requested_cf:
                    self._switch_to_emission_shader(material, value)
                elif key_copy == "infuse_texture" and requested_cf:
                    MaterialManipulator._infuse_texture(material, value)
                elif key_copy == "infuse_material" and requested_cf:
                    MaterialManipulator._infuse_material(material, value)
                elif key_copy == "add_dust" and requested_cf:
                    self._add_dust_to_material(material, value)
                elif "set_" in key_copy and requested_cf:
                    # sets the value of the principled shader
                    self._op_principled_shader_value(material, key_copy[len("set_"):], value, "set")
                elif "add_" in key_copy and requested_cf:
                    # sets the value of the principled shader
                    self._op_principled_shader_value(material, key_copy[len("add_"):], value, "add")
                elif hasattr(material, key_copy):
                    # set the value
                    setattr(material, key_copy, value)

    def _get_the_set_params(self, params_conf: Config) -> dict:
        """ Extracts actual values to set from a Config object.

        :param params_conf: Object with all user-defined data.
        :return: Parameters to set as {name of the parameter: it's value} pairs.
        """
        params = {}
        for key in params_conf.data.keys():
            result = None
            if key == "cf_color_link_to_displacement":
                result = params_conf.get_float(key)
            elif key == "cf_change_to_vertex_color":
                result = params_conf.get_string(key)
            elif key == "cf_textures":
                result = {}
                paths_conf = Config(params_conf.get_raw_dict(key))
                for text_key in paths_conf.data.keys():
                    text_path = paths_conf.get_string(text_key)
                    result.update({text_key: text_path})
            elif key == "cf_switch_to_emission_shader":
                result = {}
                emission_conf = Config(params_conf.get_raw_dict(key))
                for emission_key in emission_conf.data.keys():
                    if emission_key == "color":
                        attr_val = emission_conf.get_list("color", [1, 1, 1, 1])
                    elif emission_key == "strength":
                        attr_val = emission_conf.get_float("strength", 1.0)
                    result.update({emission_key: attr_val})
            elif key == "cf_infuse_texture":
                result = Config(params_conf.get_raw_dict(key))
            elif key == "cf_infuse_material":
                result = Config(params_conf.get_raw_dict(key))
            elif key == "cf_add_dust":
                result = params_conf.get_raw_dict(key)
            elif "cf_set_" in key or "cf_add_" in key:
                result = params_conf.get_raw_value(key)
            else:
                result = params_conf.get_raw_value(key)

            params.update({key: result})

        return params

    def _load_textures(self, text_paths: dict) -> dict:
        """ Loads textures.

        :param text_paths: Texture data.
        :return: Loaded texture data.
        """
        loaded_textures = {}
        for key in text_paths.keys():
            bpy.ops.image.open(filepath=text_paths[key], directory=os.path.dirname(text_paths[key]))
            loaded_textures.update({key: bpy.data.images.get(os.path.basename(text_paths[key]))})

        return loaded_textures

    def _set_textures(self, loaded_textures: dict, material: Material):
        """ Creates a ShaderNodeTexImage node, assigns a loaded image to it and connects it to the shader of the
            selected material.

        :param loaded_textures: Loaded texture data.
        :param material: Material to be modified.
        """
        # for each Image Texture node set a texture (image) if one was loaded
        for key, texture in loaded_textures.items():
            material.set_principled_shader_value(key, texture)

    @staticmethod
    def _op_principled_shader_value(material: Material, shader_input_key: str, value: Any, operation: str):
        """
        Sets or adds the given value to the shader_input_key of the principled shader in the material

        :param material: Material to be modified.
        :param shader_input_key: Name of the shader's input.
        :param value: Value to set.
        """
        principled_bsdf = material.get_the_one_node_with_type("BsdfPrincipled")
        shader_input_key_copy =  shader_input_key.replace("_", " ").upper() if shader_input_key.replace("_", " ").title() == "Ior" else shader_input_key.replace("_", " ").title()
        if principled_bsdf.inputs[shader_input_key_copy].links:
            material.links.remove(principled_bsdf.inputs[shader_input_key_copy].links[0])
        if shader_input_key_copy in principled_bsdf.inputs:
            if operation == "set":
                principled_bsdf.inputs[shader_input_key_copy].default_value = value
            elif operation == "add":
                if isinstance(principled_bsdf.inputs[shader_input_key_copy].default_value, float):
                    principled_bsdf.inputs[shader_input_key_copy].default_value += value
                else:
                    if len(principled_bsdf.inputs[shader_input_key_copy].default_value) != len(value):
                        raise Exception(f"The shapder input key '{shader_input_key_copy}' needs a value with "
                                        f"{len(principled_bsdf.inputs[shader_input_key_copy].default_value)} "
                                        f"dimensions, the used config value only has {len(value)} dimensions.")
                    for i in range(len(principled_bsdf.inputs[shader_input_key_copy].default_value)):
                        principled_bsdf.inputs[shader_input_key_copy].default_value[i] += value[i]
        else:
            raise Exception("Shader input key '{}' is not a part of the shader.".format(shader_input_key_copy))

    @staticmethod
    def _link_color_to_displacement_for_mat(material: Material, multiply_factor: float):
        """ Link the output of the texture image to the displacement. Fails if there is more than one texture image.

        :param material: Material to be modified.
        :param multiply_factor: Multiplication factor of the displacement.
        """
        material.set_displacement_from_principled_shader_value("Base Color", multiply_factor)

    @staticmethod
    def _map_vertex_color(material: Material, layer_name: str, active_shading: bool = True):
        """ Replaces the material with a mapping of the vertex color to a background color node.

        :param material: Material to be modified.
        :param layer_name: Name of the vertex color layer.
        :param active_shading: Whether to keep the principled bsdf shader. If True, the material properties influence light
                               reflections such as specularity, roughness, etc. alter the object's appearance. Type: bool.

        """
        material.map_vertex_color(layer_name, active_shading)

    def _switch_to_emission_shader(self, material: Material, value: dict):
        """ Adds the Emission shader to the target material, sets it's color and strength values, connects it to
            the Material Output node.

        :param material: Material to be modified.
        :param value: Light color and strength data.
        """
        material.make_emissive(emission_strength=value["strength"], emission_color=value["color"], replace=True, keep_using_base_color=False)

    @staticmethod
    def _infuse_texture(material: Material, config: Config):
        """
        Overlays the selected material with a texture, this can be either a color texture like for example dirt or
        it can be a texture, which is used as an input to the Principled BSDF of the given material.

        :param material: Material, which will be changed
        :param config: containing the config information
        """
        used_mode = config.get_string("mode", "overlay")
        used_textures = config.get_list("used_texture")
        invert_texture = config.get_bool("invert_texture", False)
        used_connector = config.get_string("connection", "Base Color")
        texture_scale = config.get_float("texture_scale", 0.05)
        strength = config.get_float("strength", 0.5)

        if config.has_param("strength") and used_mode == "set":
            raise Exception("The strength can only be used if the mode is not \"set\"!")

        if len(used_textures) == 0:
            raise Exception(f"You have to select a texture, which is {used_mode} over the material!")
        texture = random.choice(used_textures)

        material.infuse_texture(
            texture=texture,
            mode=used_mode,
            invert_texture=invert_texture,
            connection=used_connector,
            texture_scale=texture_scale,
            strength=strength
        )


    @staticmethod
    def _infuse_material(material: Material, config: Config):
        """
        Infuse a material inside of another material. The given material, will be adapted and the used material, will
        be added, depending on the mode either as add or as mix. This change is applied to all outputs of the material,
        this include the Surface (Color) and also the displacement and volume. For displacement mix means multiply.

        :param material: Used material
        :param config: Used config
        """
        # determine the mode
        used_mode = config.get_string("mode", "mix")

        mix_strength = 0.0
        if used_mode == "mix":
            mix_strength = config.get_float("mix_strength", 0.5)
        elif used_mode == "add" and config.has_param("mix_strength"):
            raise Exception("The mix_strength only works in the mix mode not in the add mode!")

        # get the material, which will be used to infuse the given material
        used_materials = config.get_list("used_material")
        used_material = random.choice(used_materials)

        material.infuse_material(
            material=Material(used_material),
            mode=used_mode,
            mix_strength=mix_strength
        )

    def _add_dust_to_material(self, material: Material, value: dict):
        """
        Adds a dust film to the material, where the strength determines how much dust is used.

        This will be added right before the output of the material.

        :param material: Used material
        :param value: dict with all used keys
        """

        # extract values from the config, like strength, texture_scale and used_dust_texture
        config = Config(value)
        strength = config.get_float("strength")
        texture_scale = config.get_float("texture_scale", 0.1)
        # if no texture is used, a random noise texture is generated
        texture_nodes = config.get_list("used_dust_texture", None)

        Dust.add_dust(
            material=material,
            strength=strength,
            texture_nodes=texture_nodes,
            texture_scale=texture_scale
        )
