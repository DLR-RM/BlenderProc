import numpy as np
import bpy

from src.main.Module import Module

class Dist2Depth(Module):
    """ Transforms Distance Image Rendered using Mist/Z pass to a depth image"""
    def __init__(self, config):
        Module.__init__(self, config)

    def run(self, dist):
        """
        :param dist: The distance data.
        :return: The depth data.
        """
        if len(dist.shape) > 2:
            dist = dist[:, :, 0] # All channles have the same value, so just extract any single channel
        else:
            dist = dist.squeeze()
        
        height, width = dist.shape

        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        max_resolution = max(width, height) 

        # Compute Intrinsics from Blender attributes (can change)
        f = width / (2 * np.tan(cam.angle / 2.))
        cx = width / 2. - cam.shift_x * max_resolution
        cy = height / 2. + cam.shift_y * max_resolution

        xs, ys = np.meshgrid(np.arange(dist.shape[1]), np.arange(dist.shape[0]))
        
        # coordinate distances to principal point
        x_opt = np.abs(xs-cx)
        y_opt = np.abs(ys-cy)

        # Solve 3 equations in Wolfram Alpha: 
        # Solve[{X == (x-c0)/f0*Z, Y == (y-c1)/f0*Z, X*X + Y*Y + Z*Z = d*d}, {X,Y,Z}]
        depth = dist * f / np.sqrt(x_opt**2 + y_opt**2 + f**2)

        return depth

