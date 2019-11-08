import mathutils
import numpy as np
import src.utility.BlenderUtility


class POIGetter:
    """ Computes a median point of interest in the scene based on bounding boxes of all objects in the scene.
    """

    @staticmethod
    def get():
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
            mean_bb_points = np.vstack([mean_bb_points, np.mean(bb_points, axis = 0)])

        # Calculate median point
        median_bb_point = mathutils.Vector(np.median(objs_bb_points, axis = 0))

        return median_bb_point
