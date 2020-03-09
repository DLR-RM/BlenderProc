import numpy as np

from src.main.Provider import Provider


class Value(Provider):
    """ Sampling 1-d value of bool, int, or float type.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "type", "The type of a value to sample. Type: string. Available options: float, int, boolean.
       "min", "The minimum value. Optional. Type: float. int."
       "max", "The maximum value (excluded frm the defined range of values). Type: float, int."
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Sampled value. Type: Mathutils Vector
        """
        # get type of the value to sample
        val_type = self.config.get_string("type")
        # sample bool
        if val_type.lower() == 'bool' or val_type.lower() == 'boolean':
            val = bool(np.random.randint(0, 2))
        # or sample int
        elif val_type.lower() == 'int':
            val_min = self.config.get_int('min')
            val_max = self.config.get_int('max')
            val = np.random.randint(val_min, val_max)
        # or sample float
        elif val_type.lower() == 'float':
            val_min = self.config.get_float('min')
            val_max = self.config.get_float('max')
            val = np.random.uniform(val_min, val_max)
        else:
            raise Exception("Cannot sample this type: " + val_type)

        return val
