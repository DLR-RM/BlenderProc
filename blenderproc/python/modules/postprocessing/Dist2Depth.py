from blenderproc.python.modules.main.Module import Module
from blenderproc.python.postprocessing.PostProcessingUtility import dist2depth


class Dist2Depth(Module):
    """ Transforms Distance Image Rendered using Mist/Z pass to a depth image.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - depth_output_key
          - The key which should be used for storing the output data in a merged file. Default: 'depth'.
          - string
    """
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, dist, key, version):
        """
        :param dist: The distance data.
        :param key: The key used to store distance data.
        :param version: Version of the produced distance data.
        :return: The depth data, an appropriate key and version.
        """
        depth = dist2depth(dist)
        output_key = self.config.get_string("depth_output_key", "depth")
        version = "1.0.0"
        return depth, output_key, version
