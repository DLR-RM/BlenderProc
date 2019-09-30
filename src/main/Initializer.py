from src.main.Module import Module
import bpy

class Initializer(Module):

    def __int__(self, config):
        Module.__init__(self, config)

    def run(self):
        """ Does some basic initialization of the blender project.

         - Sets background color
         - Configures computing device
         - Creates camera
        """
        # Make sure to use the current GPU
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
        bpy.context.scene.frame_end = 1
        print(prefs.compute_device_type, prefs.get_devices())
        for group in prefs.get_devices():
            for d in group:
                d.use = True

        # Set background color
        world = bpy.data.worlds['World']
        world.color[:3] = self.config.get_list("horizon_color", [0.535, 0.633, 0.608])

        # Create the cam
        cam = bpy.data.cameras.new("Camera")
        cam_ob = bpy.data.objects.new("Camera", cam)
        bpy.context.scene.collection.objects.link(cam_ob)
        bpy.context.scene.camera = cam_ob

        # Use cycles
        bpy.context.scene.render.engine = 'CYCLES'