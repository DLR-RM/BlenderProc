from blenderproc.python.modules.main.Provider import Provider
from blenderproc.python.sampler.Disk import disk


class DiskModule(Provider):
    """
    Samples a point on a 1-sphere (circle), or on a 2-ball (disk, i.e. circle + interior space), or on an arc/sector
    with an inner angle less or equal than 180 degrees. Returns a 3d mathutils.Vector sampled point.

    Example 1: Sample a point from a 1-sphere.

    .. code-block:: yaml

        {
          "provider": "sampler.Disk",
          "sample_from": "circle",
          "center": [0, 0, 4],
          "radius": 7
        }

    Example 1: Sample a point from a sector.

    .. code-block:: yaml

        {
          "provider": "sampler.Disk",
          "sample_from": "sector",
          "center": [0, 0, 4],
          "radius": 7,
          "start_angle": 0,
          "end_angle": 90
        }

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - center
          - Center (in 3d space) of a 2d geometrical shape to sample from.
          - mathutils.Vector
        * - radius
          - The radius of the disk.
          - float
        * - rotation
          - List of three (XYZ) Euler angles that represent the rotation of the 2d geometrical structure used for
            sampling in 3d space. Default: [0, 0, 0].
          - mathutils.Vector
        * - sample_from
          - Mode of sampling. Defines the geometrical structure used for sampling, i.e. the shape to sample from.
            Default: "disk". Available: ["disk", "circle", "sector", "arc"].
          - string
        * - start_angle
          - Start angle in degrees that is used to define a sector/arc to sample from. Must be smaller than
            end_angle. Arc's/sector's inner angle (between start and end) must be less or equal than 180 degrees.
            Angle increases in the counterclockwise direction from the positive direction of X axis. Default: 0.
          - float
        * - end_angle
          - End angle in degrees that is used to define a sector/arc to sample from. Must be bigger than
            start_angle. Arc's/sector's inner angle (between start and end) must be less or equal than 180 degrees.
            Angle increases in the counterclockwise direction from the positive direction of X axis. Default: 180.
          - float
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: A random point sampled point on a circle/disk/arc/sector. Type: mathutils.Vector.
        """
        center = self.config.get_vector3d("center")
        radius = self.config.get_float("radius")
        euler_angles = self.config.get_vector3d("rotation", [0, 0, 0])
        sample_from = self.config.get_string("sample_from", "disk")
        start_angle = self.config.get_float("start_angle", 0)
        end_angle = self.config.get_float("end_angle", 180)

        return disk(
            center=center,
            radius=radius,
            rotation=euler_angles,
            sample_from=sample_from,
            start_angle=start_angle,
            end_angle=end_angle
        )