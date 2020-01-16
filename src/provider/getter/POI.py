import mathutils
import numpy as np
import bpy

from src.main.Provider import Provider
from src.utility.BlenderUtility import get_bounds

class POI(Provider):
    """ Computes a point of interest in the scene. """

    def __init__(self, config):
        Provider.__init__(self, config)

    def run(self):
        """
        :return: Point of interest in the scene. Type: mathutils Vector.
        """
        # Init matrix for all points of all bounding boxes
        mean_bb_points = []
        # For every object in the scene
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                # Get bounding box corners
                bb_points = get_bounds(obj)
                # Compute mean coords of bounding box
                mean_bb_points.append(np.mean(bb_points, axis=0))
        # Query point - mean of means
        mean_bb_point = np.mean(mean_bb_points, axis=0)
        # Closest point (from means) to query point (mean of means)
        poi = mathutils.Vector(mean_bb_points[np.argmin(np.linalg.norm(mean_bb_points - mean_bb_point, axis = 1))])

        return poi
