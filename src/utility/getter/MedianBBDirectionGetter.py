import mathutils
import numpy as np
import src.utility.BlenderUtility


class MedianBBDirectionGetter:
    """

    """

    @staticmethod
    def get(point):
        """

        """
        objs_bb_points = np.array([]).reshape(0, 3)
        for obj in bpy.context.scene.objects:
            for bb_point in get_bounds(obj):
                objs_bb_points = np.vstack([objs_bb_points, np.array([bb_point[:]])])

        med_bb_point = np.median(objs_bb_points, axis = 0)

        vector = (med_bb_point - np.array([point[:]])).flatten()

        norm = np.sqrt(vector.dot(vector))

        forward_vector = mathutils.Vector(vector/norm)
        
        return forward_vector
