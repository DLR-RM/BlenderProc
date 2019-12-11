import mathutils
import numpy as np
import src.utility.BlenderUtility
import bpy
from src.utility.BlenderUtility import get_bounds

class POIGetter:
    """ Computes a point of interest in the scene. """

    @staticmethod
    def get(config):
        """
        :return: Point of interest in the scene. Type: mathutils Vector.
        """
        # Init matrix for all points of all bounding boxes
        mean_bb_points = np.array([]).reshape(0, 3)
        # For every object in the scene
        for obj in bpy.context.scene.objects:
            bb_points = np.array([]).reshape(0, 3)
            # For every point of a bounding box
            for point in get_bounds(obj):
                # Stack points of a bounding box
                bb_points = np.vstack([bb_points, np.array([point[:]])])
            # Stack mean coords of bounding boxes
            mean_bb_points = np.vstack([mean_bb_points, np.mean(bb_points, axis=0)])
        # Query point - mean of means
        mean_bb_point = np.mean(mean_bb_points, axis=0)
        # Closest point (from means) to query point (mean of means)
        poi = mathutils.Vector(mean_bb_points[np.argmin(np.linalg.norm(mean_bb_points - mean_bb_point, axis = 1))])
        return poi
