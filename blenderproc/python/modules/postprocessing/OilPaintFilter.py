from blenderproc.python.modules.main.Module import Module
from blenderproc.python.postprocessing.PostProcessingUtility import oil_paint_filter

class OilPaintFilter(Module):
    """
    Applies the oil paint filter on a single channel image (or more than one channel, where each channel is a replica
    of the other). This could be desired for corrupting rendered depth maps to appear more realistic. Also trims the
    redundant channels if they exist.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - filter_size
          - Mode filter size, should be an odd number. Default: 5
          - int
        * - edges_only
          - If true, applies the filter on the edges only. For RGB images, they should be represented in uint8
            arrays. Default: True
          - bool
        * - rgb
          - Apply the filter on an RGB image (if the image has 3 channels, they're assumed to not be replicated).
            Default: False
          - bool
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, image, key, version):
        filter_size = self.config.get_int("filter_size", 5)
        edges_only = self.config.get_bool("edges_only", True)
        rgb = self.config.get_bool("rgb", False)

        filtered_img = oil_paint_filter(image, filter_size, edges_only, rgb)

        return filtered_img, key, version


