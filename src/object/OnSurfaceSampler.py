import bpy
import mathutils

from src.utility.BlenderUtility import check_intersection, check_bb_intersection, get_bounds
from src.main.Module import Module


class OnSurfaceSampler(Module):
    """ Places objects on a surface. The object are positioned slightly above the surface, it is recommended to run PhysicsPositioning afterwards to make sure the objects are not hovering.

    .. csv-table::
       :header: "Parameter", "Description"

       "objects_to_sample", "Here call an appropriate Provider (Getter) in order to select objects."
       "max_iterations", "Amount of tries before giving up on an object (deleting it) and moving to the next one. Optional. Type: int. Default value: 100."
       "pos_sampler", "Here call an appropriate Provider (Sampler) in order to sample position (XYZ 3d vector) for each object. UpperRegionSampler recommended."
       "rot_sampler", "Here call an appropriate Provider (Sampler) in order to sample rotation (Euler angles 3d vector) for each object."
       "surface", "Object to place objects_to_sample on, if multiple are given only the first one is used."
       "min_distance", "Minimum distance to the closest other object. Center to center. Only objects placed by this Module considered. Type: float. Default value: 0.25"
       "max_distance", "Maximum distance to the closest other object. Center to center. Only objects placed by this Module considered. Type: float. Default value: 0.6"
       "up_direction", "Normal vector of the side of surface the objects should be placed on. Type: mathutils.Vector, Default value: Vector([0., 0., 1.])"
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
        """
        Check if all corner of the bounding box are "above" the surface
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
        """
        Check if object is not too close or too far from previous objects
        """
        closest_distance = None

        for already_placed in self.placed_objects:
            distance = (already_placed.location - obj.location).length
            if closest_distance is None or distance < closest_distance:
                closest_distance = distance

        return closest_distance is None or (self.min_distance <= closest_distance <= self.max_distance)

    @staticmethod
    def collision(a, b):
        """
        Check if a and b intersect
        """
        intersection = check_bb_intersection(a, b)
        if intersection:
            # check for more refined collisions
            intersection, cache = check_intersection(a, b)

        return intersection

    def check_collision_free(self, obj):
        """
        Check if object collides with none of the previous objects
        """
        for already_placed in self.placed_objects:
            if self.collision(obj, already_placed):
                return False

        return True

    def drop(self, obj):
        """
        Move object "down" until its bounding box touches the bounding box of the surface (not precise)
        """
        obj_bounds = get_bounds(obj)
        obj_height = min([self.up_direction.dot(corner) for corner in obj_bounds])

        obj.location = obj.location - self.up_direction * (obj_height - self.surface_height)
        bpy.context.view_layer.update()

    def run(self):
        max_tries = self.config.get_int("max_iterations", 100)
        objects = self.config.get_list("objects_to_sample")
        self.surface = self.config.get_list("surface")[0]

        surface_bounds = get_bounds(self.surface)
        self.surface_height = max([self.up_direction.dot(corner) for corner in surface_bounds])

        for obj in objects:
            if obj.type == "MESH":

                print("Trying to put ", obj.name)

                places_successfully = False

                for i in range(max_tries):
                    position = self.config.get_vector3d("pos_sampler")
                    rotation = self.config.get_vector3d("rot_sampler")

                    obj.location = position
                    obj.rotation_euler = rotation
                    bpy.context.view_layer.update()

                    good_position = True

                    if not self.check_collision_free(obj):
                        print("Collision detected, retrying!")
                        continue

                    if good_position and not self.check_above_surface(obj):
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

                    print("Placed object \"{}\" successfully at {} after {} iterations!".format(obj.name, obj.location, i+1))
                    self.placed_objects.append(obj)

                    places_successfully = True
                    break

                if not places_successfully:
                    print("Giving up on {}, deleting...".format(obj.name))
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.ops.object.delete()
                    bpy.context.view_layer.update()
