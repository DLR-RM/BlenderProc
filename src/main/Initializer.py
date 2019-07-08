from src.main.Module import Module
import bpy

class Initializer(Module):

    def __int__(self, config):
        Module.__init__(self, config)

    def run(self):
        # Make sure to use the current GPU
        prefs = bpy.context.user_preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
        print(prefs.compute_device_type, prefs.get_devices())
        for group in prefs.get_devices():
            for d in group:
                d.use = True

        # Set background color
        world = bpy.data.worlds['World']
        world.horizon_color[:3] = (0.535, 0.633, 0.608)

        # Create the cam
        cam = bpy.data.cameras.new("Camera")
        cam_ob = bpy.data.objects.new("Camera", cam)
        bpy.context.scene.objects.link(cam_ob)
        self.scene.camera = cam_ob

        # Use cycles
        self.scene.render.engine = 'CYCLES'