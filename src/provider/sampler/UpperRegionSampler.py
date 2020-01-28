import mathutils
import random
import bpy
import math

from src.main.Provider import Provider
from src.utility.BlenderUtility import get_bounds


class UpperRegionSampler(Provider):
    """ Uniformly samples a 3-dimensional value over the bounding box of the specified objects.

    This will lead to an parallelepiped (similar to a cube, which uses parallelograms as faces) in which the
    values are uniformly sampled.

    The face closest to the bounding box is the face, which goes away either in the upper direction or the normal
    direction of this particular face. The upper direction vector defines, where is up in the scene.
    If the min_height is not zero the closest face to the bounding box is moved by min_height away either in upper
    direction or in normal direction of the face.

    The face, which is furthest away is defined by the max_height and has the same normal as the closest face to the
    bounding box.

    **Configuration**:
    .. csv-table::
        :header: "Parameter", "Description"
        "to_sample_on": "Selector (getter.Object), which gives a selection of object, which are used to sample on"
        "min_height", "float, this is the minimum distance to the bounding box that a point is sampled on"
        "max_height", "float, this is the maximum distance to the bounding box that a point is sampled on"
        "upper_dir", "the upper direction of the sampling box,
                            possible values [float, float, float], default: [0.0, 0.0, 1.0]"
        "use_upper_dir", "the sampling above the selected surface, can be done with the upper_dir or
                            with the face normal, if this is true the upper_dir is used: default: True"
        "use_ray_trace_check", "When this is true, a ray is cast towards the sampled object and only if the object
                            is directly below the sampled position is the position accepted. default: False"
    """
    def __init__(self, config):
        Provider.__init__(self, config)
        self._regions = []

        # invoke a Getter, get a list of objects to manipulate
        self._objects = config.get_list("to_sample_on")
        if len(self._objects) == 0:
            raise Exception("The used selector returns an empty list, check the config value: \"to_sample_on\"")

        # min and max distance to the bounding box
        self._min_height = config.get_float("min_height", 0.0)
        self._max_height = config.get_float("max_height", 1.0)
        if self._max_height < self._min_height:
            raise Exception("The minimum height ({}) must be smaller "
                            "than the maximum height ({})!".format(self._min_height, self._max_height))
        self._use_ray_trace_check = config.get_bool('use_ray_trace_check', False)

        # the upper direction, to define what is up in the scene
        # is used to selected the correct face
        self._upper_dir = config.get_vector3d("upper_dir", [0.0, 0.0, 1.0])
        self._upper_dir.normalize()
        # if this is true the up direction is determined by the upper_dir vector, if it is false the
        # face normal is used
        self._use_upper_dir = config.get_bool("use_upper_dir", True)

        def calc_vec_and_normals(face):
            """
            Calculates the two vectors, which lie in the plane of the face and the normal of the face
            :param face: [4x[3xfloat]] four corner coordinates of a face
            :return: (two vectors in the plane), and the normal
            """
            vec1 = face[1] - face[0]
            vec2 = face[3] - face[0]
            normal = vec1.cross(vec2)
            normal.normalize()
            return (vec1, vec2), normal

        # determine for each object in objects the region, where to sample on
        for obj in self._objects:
            bb = get_bounds(obj)
            faces = []
            faces.append([bb[0], bb[1], bb[2], bb[3]])
            faces.append([bb[0], bb[4], bb[5], bb[1]])
            faces.append([bb[1], bb[5], bb[6], bb[2]])
            faces.append([bb[6], bb[7], bb[3], bb[2]])
            faces.append([bb[3], bb[7], bb[4], bb[0]])
            faces.append([bb[7], bb[6], bb[5], bb[4]])
            # select the face, which has the smallest angle to the upper direction
            min_diff_angle = 2 * math.pi
            selected_face = None
            for face in faces:
                # calc the normal of all faces
                _, normal = calc_vec_and_normals(face)
                diff_angle = math.acos(normal.dot(self._upper_dir))
                if diff_angle < min_diff_angle:
                    min_diff_angle = diff_angle
                    selected_face = face
            # save the selected face values
            if selected_face is not None:
                vectors, normal = calc_vec_and_normals(selected_face)
                base_point = mathutils.Vector(selected_face[0])
                self._regions.append(Region2D(vectors, normal, base_point))
            else:
                raise Exception("Couldn't find a face, for this obj: {}".format(obj.name))


    def run(self):
        """
        Samples based on the description above
        :return: Sampled value. Type: mathutils.Vector
        """

        if self._regions and len(self._regions) == len(self._objects):
            selected_region_id = random.randint(0, len(self._regions))
            while True:
                selected_region, obj = self._regions[selected_region_id], self._objects[selected_region_id]
                ret = selected_region.sample_point()
                dir = self._upper_dir if self._use_upper_dir else selected_region.normal()
                ret += dir * random.uniform(self._min_height, self._max_height)
                if self._use_ray_trace_check:
                    # check if the object was hit
                    hit, _, _, _ = obj.ray_trace(ret, dir * -1.0)
                    if hit:  # if the object was hit return
                        break
                else:
                    break
            return ret
        else:
            # if the init failed return [0,0,0]
            return mathutils.Vector([0,0,0])



class Region2D(object):
    """
    Helper class for UpperRegionSampler:
    Defines a 2D region in 3D
    """

    def __init__(self, vectors, normal, base_point):
        self._vectors = vectors  # the two vectors which lie in the selected face
        self._normal = normal  # the normal of the selected face
        self._base_point = base_point  # the base point of the selected face

    def sample_point(self):
        """
        Samples a point in the 2D Region
        :return:
        """
        ret = self._base_point.copy()
        # walk over both vectors in the plane and determine a distance in both direction
        for vec in self._vectors:
            ret += vec * random.uniform(0.0, 1.0)
        return ret

    def normal(self):
        """
        :return: the normal of the region
        """
        return self._normal



