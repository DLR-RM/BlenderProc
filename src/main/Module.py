import bpy

class Module:

    def __init__(self, config):
        self.config = config
        self.scene = bpy.data.scenes["Scene"]