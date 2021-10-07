from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.sampler.UniformSO3 import uniformSO3


class UniformSO3Module(Provider):
    """ Uniformly samples rotations from SO(3). Allows to limit the rotation around Blender World coordinate axes.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - around_x
          - Whether to rotate around X-axis. Default: True.
          - bool
        * - around_y
          - Whether to rotate around Y-axis. Default: True.
          - bool
        * - around_z
          - Whether to rotate around Z-axis. Default: True.
          - bool
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Sampled rotation in euler angles. Type: mathutils.Vector
        """
        # Indicators of which axes to rotate around.
        around_x = self.config.get_bool('around_x', True)
        around_y = self.config.get_bool('around_y', True)
        around_z = self.config.get_bool('around_z', True)

        return uniformSO3(around_x, around_y, around_z)