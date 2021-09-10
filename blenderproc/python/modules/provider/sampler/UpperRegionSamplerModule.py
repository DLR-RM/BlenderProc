
from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.types.MeshObjectUtility import convert_to_meshes
from blenderproc.python.sampler.UpperRegionSampler import upper_region


class UpperRegionSamplerModule(Provider):
    """
    Uniformly samples 3-dimensional value over the bounding box of the specified objects (can be just a plane) in the
    defined upper direction. If "use_upper_dir" is False, samples along the face normal closest to "upper_dir". The
    sampling volume results in a parallelepiped. "min_height" and "max_height" define the sampling distance from the face.

    Example 1: Sample a location on the surface of the first object to match the name pattern with height above this
    surface in range of [1.5, 1.8].

    .. code-block:: yaml

        {
          "provider": "sampler.UpperRegionSampler",
          "min_height": 1.5,
          "max_height": 1.8,
          "to_sample_on": {
            "provider": "getter.Entity",
            "index": 0,
            "conditions": {
              "name": "Table.*"
            }
          }
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - to_sample_on
          - Objects, on which to sample on.
          - Provider
        * - min_height
          - Minimum distance to the bounding box that a point is sampled on. Default: 0.0.
          - float
        * - max_height
          - Maximum distance to the bounding box that a point is sampled on. Default: 1.0.
          - float
        * - face_sample_range
          - Restricts the area on the face where objects are sampled. Specifically describes relative lengths of
            both face vectors between which points are sampled. Default: [0.0, 1.0]
          - list
        * - upper_dir
          - The 'up' direction of the sampling box. Default: [0.0, 0.0, 1.0].
          - list
        * - use_upper_dir
          - Toggles the sampling above the selected surface, can be done with the upper_dir or with the face normal,
            if this is true the upper_dir is used. Default: True.
          - bool
        * - use_ray_trace_check
          - Toggles using a ray casting towards the sampled object (if the object is directly below the sampled
            position is the position accepted). Default: False.
          - bool
    """
    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """ Samples based on the description above.

        :return: Sampled value. Type: mathutils.Vector
        """

        # invoke a Getter, get a list of objects to manipulate
        objects = convert_to_meshes(self.config.get_list("to_sample_on"))
        if len(objects) == 0:
            raise Exception("The used selector returns an empty list, check the self.config value: \"to_sample_on\"")

        # relative area on selected face where to sample points
        face_sample_range = self.config.get_vector2d("face_sample_range", [0.0, 1.0])

        # min and max distance to the bounding box
        min_height = self.config.get_float("min_height", 0.0)
        max_height = self.config.get_float("max_height", 1.0)
        if max_height < min_height:
            raise Exception("The minimum height ({}) must be smaller "
                            "than the maximum height ({})!".format(min_height, max_height))
        use_ray_trace_check = self.config.get_bool('use_ray_trace_check', False)

        # the upper direction, to define what is up in the scene
        # is used to selected the correct face
        upper_dir = self.config.get_vector3d("upper_dir", [0.0, 0.0, 1.0])
        upper_dir.normalize()
        # if this is true the up direction is determined by the upper_dir vector, if it is false the
        # face normal is used
        use_upper_dir = self.config.get_bool("use_upper_dir", True)

        return upper_region(
            objects_to_sample_on=objects,
            face_sample_range=face_sample_range,
            min_height=min_height,
            max_height=max_height,
            use_ray_trace_check=use_ray_trace_check,
            upper_dir=upper_dir,
            use_upper_dir=use_upper_dir
        )
