import bpy

from src.main.Module import Module
from src.utility.Config import Config
from src.utility.Utility import Utility


class HideModule(Module):
    """
    Will hide the selected objects from the scene and render frames with and without the objects.

    Example
    .. code-block:: yaml

    {
      "module": "object.HideModule",
      "config": {
        "selector": {  # this will select the object, which gets removed for the same set of frames.
          "provider": "getter.Entity",
          "conditions": {
            "name": "wall"
          }
        "number_of_frames": 2, # this specifies first n frames to be duplicated.
        },
      }
    }


    """

    def __init__(self, config: Config):
        Module.__init__(self, config)

    def run(self):
        """ Removes objects for the same set of frames.
        """

        objects = self.config.get_list("selector")
        number_of_frames = self.config.get_int("number_of_frames", bpy.context.scene.frame_end)
        if number_of_frames > bpy.context.scene.frame_end:
            number_of_frames = bpy.context.scene.frame_end
        print(f"Will use {number_of_frames} number of frames, for {len(objects)} objects.")
        # iterate over all objects
        for obj in objects:
            obj.hide_render = False
            # Insert all selected objects to each frame for normal rendering.
            for frame in range(number_of_frames):
                Utility.insert_keyframe(obj, "hide_render", frame)

            # Insert updated selected objects to each frame with the field hide_render modified
            obj.hide_render = True
            for frame in range(number_of_frames):
                Utility.insert_keyframe(obj, "hide_render", frame + bpy.context.scene.frame_end)

        # Copy and modify camera location and rotation to the new frames where objects are hidden.
        camera = bpy.context.scene.camera
        for frame in range(number_of_frames):
            bpy.context.scene.frame_set(frame)
            Utility.insert_keyframe(camera, "location", frame + bpy.context.scene.frame_end)
            Utility.insert_keyframe(camera, "rotation_euler", frame + bpy.context.scene.frame_end)
        bpy.context.scene.frame_end += number_of_frames
