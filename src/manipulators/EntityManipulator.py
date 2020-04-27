import bpy
from src.main.Module import Module
from src.utility.Config import Config


class EntityManipulator(Module):
    """ Allows basic manipulator for all entities, including Meshes, Cameras, lights, and more.
    Specify a desired getter for selecting entities in 'selector' section, then specify any desired {key: value} pairs.
    Each pair is treated like a {attribute_name:attribute_value} where attr_name is any valid name for an existing
    attribute or custom property or a name of a custom property to create, while the attr_value is an according value
    for such attribute or custom property (this value can be sampled).

    In order to set a custom property, which is also an attribute, add before the key a "cp_".
    For example: Setting a custom property of type is not possible as it will change the attribute type, so
    adding a "cp_" before the key -> "cp_type" will make it possible to set the custom property "type".

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

    "selector", "Here call an appropriate Provider so select objects to manipulate."
    "mode", "Mode of operation. Optional. Type: string. Available values: "once_for_each" (if samplers are called,
             new sampled value is set to each selected entity) and "once_for_all" (if samplers are called, value
             is sampled once and set to all selected entities)."

    **Values to set**:

    .. csv-table::
        :header: "Parameter", "Description"

        "key", "Name of the attribute/custom prop. to change as a key in {name of an attr: value to set}. Type: string."
               "In order to specify, what exactly one wants to modify (e.g. attribute, custom property, etc.):"
               "For attribute: key of the pair must be a valid attribute name of the selcted object."
               "For custom property: key of the pair must start with `cp_` prefix."
               "For custom functions: key of the pair must start with `cf_` prefix. See below for more information."
        "value", "Value of the attribute/custom prop. to set as a value in {name of an attr: value to set}."

    .. csv-table::
       :header: "Parameter", "Description"

       "cf_add_modifier", "Adds a modifier to the selected object for now we only support the Solidify modifier"
                          "Example:    "cf_add_modifier": {
                                          # make sure to use this provider to avoid conflicts with the evaluation
                                          "provider": "getter.Content",
                                          "content": {
                                            "name": "Solidify",  # name of the modifier
                                            "thickness": 0.001   # attributes to be changed for this modifier
                                          }
                                        }"
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ 'Selects' entities and sets according values for defined attributes/custom properties."""
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
            print("Warning: There were not entities in this selection, probably something went wrong.")
        else:
            print("Selected {} to change.".format(len(entities)))

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
        """
        Applies a custom function to the selected entity

        :param entity, the entity where the custom fct. should be applied
        :param key, name of the custom function
        :param result, content which should be used to apply the custom function, this value should be produced with a
                       selector (getter.Content).
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
                raise Exception("The name for the modifier is unknown: {}".format(name))
        else:
            raise Exception("This function is unknown: {}".format(key))
