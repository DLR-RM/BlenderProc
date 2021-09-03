import numpy as np

from blenderproc.python.modules.main.Provider import Provider


class Value(Provider):
    """
    Sampling 1-d value of bool, int, or float type.

    Example 1: Sample a float value from [10, 30) range.

    .. code-block:: yaml

        {
          "provider": "sampler.Value",
          "type": "float",
          "min": 10,
          "max": 30
        }

    Example 2: Sample a boolean value.

    .. code-block:: yaml

        {
          "provider": "sampler.Value",
          "type": "bool"
        }

    Example 3: Sample a float value from a normal (Gaussian) distribution.

    .. code-block:: yaml

        {
          "provider": "sampler.Value",
          "type": "float",
          "mode": "normal",
          "mean": 0.0,
          "std_dev": 0.7
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - type
          - The type of a value to sample. Available: 'float', 'int', 'boolean'.
          - string
        * - mode
          - The way of how to sample values. Default: 'uniform'. Available: 'uniform', 'normal'.
          - string
        * - min
          - The minimum value. Optional.
          - float/int
        * - max
          - The maximum value (excluded frm the defined range of values).
          - float/int
        * - mean
          - Mean (“centre”) of the normal (Gaussian) distribution.
          - float
        * - std_dev
          - Standard deviation (spread or “width”) of the normal (Gaussian) distribution.
          - float
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Sampled value. Type: mathutils.Vector
        """
        # get type of the value to sample
        val_type = self.config.get_string("type")
        mode = self.config.get_string("mode", "uniform")
        # sample bool
        if val_type.lower() == 'bool' or val_type.lower() == 'boolean':
            val = bool(np.random.randint(0, 2))
        # or sample int
        elif val_type.lower() == 'int':
            if mode == "uniform":
                val_min = self.config.get_int('min')
                val_max = self.config.get_int('max')
                val = np.random.randint(val_min, val_max)
            else:
                raise Exception("Mode {} doesn't exist".format(mode))
        # or sample float
        elif val_type.lower() == 'float':
            if mode == "uniform":
                val_min = self.config.get_float('min')
                val_max = self.config.get_float('max')
                val = np.random.uniform(val_min, val_max)
            elif mode == "normal":
                mean = self.config.get_float('mean')
                std_dev = self.config.get_float('std_dev')
                val = np.random.normal(loc=mean, scale=std_dev)
            else:
                raise Exception("Mode {} doesn't exist".format(mode))
        else:
            raise Exception("Cannot sample this type: " + val_type)

        return val
