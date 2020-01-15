import bpy
from src.main.Module import Module
from src.utility.Config import Config


class ObjectManipulator(Module):
    """

    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """

        :return:
        """
        instances = self.config.get_list("instances", [])
        for instance in instances:

            set_params = {}
            sel_objs = {}
            for key in instance.keys():
                if key != 'selector':
                    set_params[key] = instance[key]
                else:
                    sel_objs[key] = instance[key]

            params_conf = Config(set_params)
            sel_conf = Config(sel_objs)
            objects = sel_conf.get_list("selector", [])

            for key in params_conf.data.keys():
                if key in supported_attrs:
                    result = params_conf.get_vector3d(key)
                    for obj in objects:
                        setattr(obj, key, result)
                else:
                    for obj in objects:
                        result = params_conf.get
                        obj[key] = result




