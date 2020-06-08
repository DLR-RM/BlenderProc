import numpy as np

from src.main.Provider import Provider


class Value(Provider):
    """ Sampling 1-d value of bool, int, or float type.

        Example 1: Sample a float value from [10, 30) range.

        {
          "provider": "sampler.Value",
          "type": "float",
          "min": 10,
          "max": 30
        }

        Example 2: Sample a boolean value.

        {
          "provider": "sampler.Value",
          "type": "bool"
        }

        Example 3: Sample a float value from a normal (Gaussian) distribution.

        {
          "provider": "sampler.Value",
          "type": "dist",
          "mean": 0.0,
          "std_dev": 0.7
        }

    **Configuration**:

    .. csv-table::
        :header: "Parameter", "Description"

        "type", "The type of a value to sample. Type: string. Available: 'float', 'int', 'boolean', 'dist'."
        "min", "The minimum value. Optional. Type: float/int."
        "max", "The maximum value (excluded frm the defined range of values). Type: float/int."
        "mean", "Mean (“centre”) of the normal (Gaussian) distribution. Type: float."
        "std_dev", "Standard deviation (spread or “width”) of the normal (Gaussian) distribution. Type: float."
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
        elif val_type.lower() == 'dist':
            mean = self.config.get_float('mean')
            std_dev = self.config.get_float('std_dev')
            val = np.random.normal(loc=mean, scale=std_dev)
        else:
            raise Exception("Cannot sample this type: " + val_type)

        return val
