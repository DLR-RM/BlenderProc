import mathutils
import numpy as np
import src.utility.BlenderUtility


class MedianBBDirectionGetter:
    """ Computes the forward vector of an object directing to the point of interest which is a median of 8-axis bounding boxes of all objects in the scene.
        **Configuration**:

        .. csv-table::
           :header: "Parameter", "Description"

           "point", "A location of an object in the scene for which the forward vector is computed."
    """

    @staticmethod
    def get(point):
        """
        :param point: XYZ location of an object in the scene. Type: mathutils Vector.
        :return: Forward vector direction to the point of intrest. Type: mathutils Vector.
        """
        # Init matrix for all points of all bounding boxes
        objs_bb_points = np.array([]).reshape(0, 3)
        # For every object in the scene
        for obj in bpy.context.scene.objects:
            # For every point of a bounding box
            for bb_point in get_bounds(obj):
                # Stack coordinates
                objs_bb_points = np.vstack([objs_bb_points, np.array([bb_point[:]])])
        # Calculate median point
        med_bb_point = np.median(objs_bb_points, axis = 0)
        # Calculate vector from a given point
        vector = (med_bb_point - np.array([point[:]])).flatten()
        # Normalize
        forward_vector = mathutils.Vector(vector/np.sqrt(vector.dot(vector)))
        
        return forward_vector
