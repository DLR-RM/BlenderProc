import bpy

class Module:

    def __init__(self, config, undo_after_run=False):
        self.config = config
        self.undo_after_run = undo_after_run