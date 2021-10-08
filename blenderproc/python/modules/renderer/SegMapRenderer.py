from blenderproc.python.modules.renderer.RendererInterface import RendererInterface
from blenderproc.python.renderer.SegMapRendererUtility import render_segmap
from blenderproc.python.utility.Utility import Utility


class SegMapRenderer(RendererInterface):
    """
    Renders segmentation maps for each registered keypoint.

    The SegMapRenderer can render segmetation maps of any kind, it can render any information related to each object.
    This can include an instance id, which is consistent over several key frames.
    It can also be a `category_id`, which can be indicated by "class".

    This Renderer can access all custom properties or attributes of the rendered objects.
    This means it can also be used to map your own custom properties to an image or if the data can not be stored in
    an image like the name of the object in a .csv file.

    The csv file will contain a mapping between each instance id and the corresponding custom property or attribute.

    Example 1:

    .. code-block:: yaml

        config: {
            "map_by": "class"
        }

    In this example each pixel would be mapped to the corresponding category_id of the object.
    Each object then needs such a custom property! Even the background. If an object is missing one an Exception
    is thrown.

    Example 2:

    .. code-block:: yaml

        "config": {
            "map_by": ["class", "instance"]
        }

    In this example the output will be a class image and an instance image, so the output will have two channels,
    instead of one. The first will contain the class the second the instance segmentation. This also means that
    the class labels per instance are stored in a .csv file.

    Example 3:

    .. code-block:: yaml

        "config": {
            "map_by": ["class", "instance", "name"]
         }

    It is often useful to also store a mapping between the instance and these class in a dict, This happens
    automatically, when "instance" and another key is used.
    All values which can not be stored in the image are stored inside of a dict. The `name`
    attribute would be saved now in a dict as we only store ints and floats in the image.
    If no "instance" is provided and only "name" would be there, an error would be thrown as an instance mapping
    is than not possible

    Example 4:

    .. code-block:: yaml

        "config": {
            "map_by": "class"
            "default_values": {"class": 0}
         }

    It is also possible to set default values, for keys object, which don't have a certain custom property.
    This is especially useful dealing with the background, which often lacks certain object properties.


    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - map_by
          - Method to be used for color mapping. Default: "class". Available: [instance, class] or any custom 
            property or attribute.
          - string
        * - default_values
          - The default values used for the keys used in map_by. Default: {}
          - dir
        * - segcolormap_output_key
          - The key which should be used for storing the class instance to color mapping in a merged file. Default:
            "segcolormap"
          - string
        * - segcolormap_output_file_prefix
          - The file prefix that should be used when writing the class instance to color mapping to file. Default:
            instance_attribute_map
          - string
        * - output_file_prefix
          - The file prefix that should be used when writing semantic information to a file. Default: `"segmap_"`
          - string

    **Custom functions**

    All custom functions here are used inside of the map_by/default_values list.

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - cf_basename
          - Adds the basename of the object to the .csv file. The basename is the name attribute, without added
            numbers to separate objects with the same name. This is used in the map_by list.
          - None
    """

    def __init__(self, config):
        RendererInterface.__init__(self, config)

    def run(self):

        # get the type of mappings which should be performed
        map_by = self.config.get_raw_dict("map_by", "class")

        default_values = self.config.get_raw_dict("default_values", {})

        with Utility.UndoAfterExecution():
            self._configure_renderer(default_samples=1)

            if not self._avoid_output:
                render_segmap(
                    self._determine_output_dir(),
                    self._temp_dir,
                    map_by,
                    default_values,
                    self.config.get_string("output_file_prefix", "segmap_"),
                    self.config.get_string("output_key", "segmap"),
                    self.config.get_string("segcolormap_output_file_prefix", "instance_attribute_map"),
                    self.config.get_string("segcolormap_output_key", "segcolormap"),
                    use_alpha_channel=self._use_alpha_channel
                )
