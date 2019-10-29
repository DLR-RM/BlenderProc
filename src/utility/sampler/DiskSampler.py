import numpy as np
import mathutils


class DiskSampler:
    """

    """

    @staticmethod
    def sample(config):
        """

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

