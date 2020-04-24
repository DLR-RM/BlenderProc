import mathutils
import numpy as np

from src.main.Provider import Provider
from src.utility.BlenderUtility import get_bounds, get_all_mesh_objects

class POI(Provider):
    """ Computes a point of interest in the scene.


    .. csv-table::
       :header: "Parameter", "Description"
       "selector", "Instead of all objects a group of objects can be selected with the `getter.Entity` class default: all_mesh_objects"
    """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Point of interest in the scene. Type: mathutils Vector.
        """
        # Init matrix for all points of all bounding boxes
        mean_bb_points = []
        # For every selected object in the scene
        selected_objects = self.config.get_list("selector", get_all_mesh_objects())
        if len(selected_objects) == 0:
            raise Exception("No objects were selected!")

        for obj in selected_objects:
            # Get bounding box corners
            bb_points = get_bounds(obj)
            # Compute mean coords of bounding box
            mean_bb_points.append(np.mean(bb_points, axis=0))
        # Query point - mean of means
        mean_bb_point = np.mean(mean_bb_points, axis=0)
        # Closest point (from means) to query point (mean of means)
        poi = mathutils.Vector(mean_bb_points[np.argmin(np.linalg.norm(mean_bb_points - mean_bb_point, axis=1))])

        return poi
