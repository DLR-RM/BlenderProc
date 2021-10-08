from blenderproc.python.modules.loader.LoaderInterface import LoaderInterface
from blenderproc.python.loader.ReplicaLoader import load_replica


class ReplicaLoaderModule(LoaderInterface):
    """ Just imports the objects for the given file path

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - data_path
          - The path to the data folder, where all rooms are saved.
          - string
        * - data_set_name
          - Name of the room (for example: apartment_0).
          - string
        * - use_smooth_shading
          - Enable smooth shading on all surfaces, instead of flat shading. Default: False.
          - bool
    """
    def __init__(self, config):
        LoaderInterface.__init__(self, config)

    def run(self):
        loaded_objects = load_replica(
            data_path=self.config.get_string('data_path'),
            data_set_name=self.config.get_string('data_set_name'),
            use_smooth_shading=self.config.get_bool('use_smooth_shading', False)
        )

        # Set the physics property of all imported objects
        self._set_properties(loaded_objects)