import mathutils


class VectorEulerConverter:
    """ Converts up, forward or right vector to Euler angles.
    
    **Configuration**:

    .. csv-table::
       :header:, "Parameter", "Description"

       "vector", "Normalized up, forward or right vector."
       "vector_type", "Set of 3 Euler angles."
    """

    @staticmethod
    def run(vector, vector_type):
    """ 
    :param vector: An up, forward or right normilized vector. Type: mathutils Vector.
    :param vector_type: Type of an input vector: UP, FORWARD or RIGHT. Type: string.
    :return: Corresponding Euler angles triplet. Type: mathutils Euler.
    """
    if vector_type == "UP":
        euler_angles = vector.to_track_quat('Z', 'Y').to_euler()
    elif vector_type == "FORWARD":
        euler_angles = vector.to_track_quat('-Z', 'Y').to_euler()
    elif vector_type == "RIGHT":
        euler_angles = vector.to_track_quat('X', 'Y').to_euler()
    else:
        raise Exception("Unknown vector type: " + vector_type)

    return euler_angles
