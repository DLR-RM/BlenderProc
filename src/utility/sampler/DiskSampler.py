import numpy as np
import mathutils


class DiskSampler:
    """ Samples a point from the circle or form the disk.

    **Configuration**:

    .. csv-table::
       :header:, "Parameter", "Description"

       "center", "A list of three values, descriving x, y and z coordinates of the center of a 2-ball."
       "radius", "The radius of the disk."
       "mode", "Mode of sampling. CIRCLE - sampling from the 1-sphere, DISK - sampling from the 2-ball."
    """

    @staticmethod
    def sample(config):
        """
        :param config: A configuration object containing the parameters necessary to sample.
        :return: A random point lying inside or on the surface of a solid sphere. Type: Mathutils vector
        """
        # Center of the disk.
        center = np.array(config.get_list("center"))
        # Radius of the disk.
        radius = config.get_float("radius")
        # Mode of operation.
        mode = config.get_string("mode")

        # Sample directions
        direction = np.random.normal(size=2)

        if np.count_nonzero(direction)==0:
            direction[0] = 1e-5

        # For normalization
        norm = direction.dot(direction)**(0.5)

        # If sampling from the circle set magnitude to radius of the disk
        if mode == "CIRCLE":
            magnitude = radius
        # If sampling from a disk set it to scaled radius
        elif mode == "DISK":
            magnitude = radius * np.random.uniform()**(1./2)
        else:
            raise Exception("Unknown sampling mode: " + mode)

        # Normilize
        sampled_point = list(map(lambda x: magnitude*x/norm, direction))

        #Add center
        location = mathutils.Vector(np.append(np.array(sampled_point), 0) + center)

        return location

