import bpy
import mathutils

from src.main.Module import Module
from src.utility.BlenderUtility import check_intersection, check_bb_intersection, get_bounds


class OnSurfaceSampler(Module):
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

        self.up_direction = config.get_vector3d("up_direction", mathutils.Vector([0., 0., 1.])).normalized()

        self.min_distance = config.get_float("min_distance", 0.25)
        self.max_distance = config.get_float("max_distance", 0.6)

        self.placed_objects = []
        self.surface = None
        self.surface_height = None

    def check_above_surface(self, obj):
        """ Check if all corners of the bounding box are "above" the surface

        :param obj: Object for which the check is carried out. Type: blender object.
        :return: True if the bounding box is above the surface, False - if not.
        """
        inv_world_matrix = self.surface.matrix_world.inverted()

        for point in get_bounds(obj):
            ray_start = inv_world_matrix @ (point + self.up_direction)
            ray_direction = inv_world_matrix @ (self.surface.location + (-1 * self.up_direction))

            is_hit, hit_location, _, _ = self.surface.ray_cast(ray_start, ray_direction)

            if not is_hit:
                return False

        return True

    def check_spacing(self, obj):
        """ Check if object is not too close or too far from previous objects.

        :param obj: Object for which the check is carried out. Type: blender object.
        :return:
        """
        closest_distance = None

        for already_placed in self.placed_objects:
            distance = (already_placed.location - obj.location).length
            if closest_distance is None or distance < closest_distance:
                closest_distance = distance

        return closest_distance is None or (self.min_distance <= closest_distance <= self.max_distance)

    @staticmethod
    def collision(first_obj, second_obj):
        """ Checks if two object intersect.

        :param first_obj: The first object for which the check is carried out. Type: blender object.
        :param second_obj: The second object for which the check is carried out. Type: blender Object.
        :return: True if objects are intersecting, if not - False.
        """
        intersection = check_bb_intersection(first_obj, second_obj)
        if intersection:
            # check for more refined collisions
            intersection, cache = check_intersection(first_obj, second_obj)

        return intersection

    def check_collision_free(self, obj):
        """ Checks if the object collides with none of the previously placed objects.

        :param obj: Object for which the check is carried out. Type: blender object.
        :return: True if object is collision free, if not - False.
        """
        for already_placed in self.placed_objects:
            if self.collision(obj, already_placed):
                return False

        return True

    def drop(self, obj):
        """ Moves object "down" until its bounding box touches the bounding box of the surface. This uses bounding boxes
            which are not aligned optimally, this will cause objects to be placed slightly to high.

        :param obj: Object to move. Type: blender object.
        """
        obj_bounds = get_bounds(obj)
        obj_height = min([self.up_direction.dot(corner) for corner in obj_bounds])

        obj.location -= self.up_direction * (obj_height - self.surface_height)

    def run(self):
        """ Samples the selected objects poses on a selected surface. """
        max_tries = self.config.get_int("max_iterations", 100)
        objects = self.config.get_list("objects_to_sample")
        self.surface = self.config.get_list("surface")
        if len(self.surface) > 1:
            raise Exception("This module operates with only one `surface` object while more than one was returned by "
                            "the Provider. Please, configure the corresponding Provider's `conditions` accordingly such "
                            "that it returns only one object! Tip: use getter.Entity's 'index' parameter.")
        else:
            self.surface = self.surface[0]

        surface_bounds = get_bounds(self.surface)
        self.surface_height = max([self.up_direction.dot(corner) for corner in surface_bounds])

        for obj in objects:
            if obj.type == "MESH":

                print("Trying to put ", obj.name)

                placed_successfully = False

                for i in range(max_tries):
                    position = self.config.get_vector3d("pos_sampler")
                    rotation = self.config.get_vector3d("rot_sampler")

                    obj.location = position
                    obj.rotation_euler = rotation

                    if not self.check_collision_free(obj):
                        print("Collision detected, retrying!")
                        continue

                    if not self.check_above_surface(obj):
                        print("Not above surface, retrying!")
                        continue

                    self.drop(obj)

                    if not self.check_above_surface(obj):
                        print("Not above surface after drop, retrying!")
                        continue

                    if not self.check_spacing(obj):
                        print("Bad spacing after drop, retrying!")
                        continue

                    if not self.check_collision_free(obj):
                        print("Collision detected after drop, retrying!")
                        continue

                    print("Placed object \"{}\" successfully at {} after {} iterations!".format(obj.name, obj.location,
                                                                                                i + 1))
                    self.placed_objects.append(obj)

                    placed_successfully = True
                    break

                if not placed_successfully:
                    print("Giving up on {}, deleting...".format(obj.name))
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.ops.object.delete()

        bpy.context.view_layer.update()
