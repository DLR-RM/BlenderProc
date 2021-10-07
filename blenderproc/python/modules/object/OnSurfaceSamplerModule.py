import mathutils

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.types.MeshObjectUtility import MeshObject, convert_to_meshes
from blenderproc.python.object.OnSurfaceSampler import sample_poses_on_surface


class OnSurfaceSamplerModule(Module):
    """ Samples objects poses on a surface.
        The objects are positioned slightly above the surface due to the non-axis aligned nature of used bounding boxes
        and possible non-alignment of the sampling surface (i.e. on the X-Y hyperplane, can be somewhat mitigated with
        precise "up_direction" value), which leads to the objects hovering slightly above the surface. So it is
        recommended to use the PhysicsPositioning module afterwards for realistically looking placements of objects on 
        the sampling surface.

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - objects_to_sample
          - Here call an appropriate Provider (Getter) in order to select objects.
          - provider
        * - max_iterations
          - Amount of tries before giving up on an object (deleting it) and moving to the next one. Default: 100.
          - int
        * - pos_sampler
          - Here call an appropriate Provider (Sampler) in order to sample position (XYZ 3d vector) for each object.
            UpperRegionSampler recommended. 
          - Provider
        * - rot_sampler
          - Here call an appropriate Provider (Sampler) in order to sample rotation (Euler angles 3d vector) for
            each object. 
          - Provider
        * - surface
          - Object to place objects_to_sample on, here call an appropriate Provider (getter) which is configured
            such that it returns only one object. 
          - Provider
        * - min_distance
          - Minimum distance to the closest other object. Center to center. Only objects placed by this Module
            considered. Default: 0.25
          - float
        * - max_distance
          - Maximum distance to the closest other object. Center to center. Only objects placed by this Module
            considered. Default: 0.6
          - float
        * - up_direction
          - Normal vector of the side of surface the objects should be placed on. Default: [0., 0., 1.].
          - mathutils.Vector
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Samples the selected objects poses on a selected surface. """

        # Collect parameters
        up_direction = self.config.get_vector3d("up_direction", mathutils.Vector([0., 0., 1.])).normalized()
        min_distance = self.config.get_float("min_distance", 0.25)
        max_distance = self.config.get_float("max_distance", 0.6)
        max_tries = self.config.get_int("max_iterations", 100)
        objects = convert_to_meshes(self.config.get_list("objects_to_sample"))
        surface = self.config.get_list("surface")
        if len(surface) > 1:
            raise Exception("This module operates with only one `surface` object while more than one was returned by "
                            "the Provider. Please, configure the corresponding Provider's `conditions` accordingly such "
                            "that it returns only one object! Tip: use getter.Entity's 'index' parameter.")
        else:
            surface = MeshObject(surface[0])

        # Define method to sample new object poses
        def sample_pose(obj: MeshObject):
            obj.set_location(self.config.get_vector3d("pos_sampler"))
            obj.set_rotation_euler(self.config.get_vector3d("rot_sampler"))

        # Sample objects on the given surface
        sample_poses_on_surface(
            objects_to_sample=objects,
            surface=surface,
            sample_pose_func=sample_pose,
            max_tries=max_tries,
            min_distance=min_distance,
            max_distance=max_distance,
            up_direction=up_direction
        )
