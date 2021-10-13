import bpy

from blenderproc.python.modules.main.Module import Module
from blenderproc.python.modules.utility.Config import Config
from blenderproc.python.utility.Utility import Utility


class HideModule(Module):
    """
    Will hide the selected objects from the scene and render frames with and without the objects.
    Be aware that this doubles the amount of used camera poses.

    If number_of_frames is lower than the amount of used camera poses the results might not be as expected.

    Example 1, here the object name "wall" will be shown in the first two frames and then hidden in the third and
    fourth frame. In this example there were only two camera poses before this module was called.

    .. code-block:: yaml

        {
          "module": "object.HideModule",
          "config": {
            "selector": {  # this will select the object, which gets removed for the same set of frames.
              "provider": "getter.Entity",
              "conditions": {
                "name": "wall"
              }
            },
            "number_of_frames": 2, # this specifies first n frames to be duplicated, this is optional
          }
        }

    **Configuration**:

    .. list-table::
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - selector
          - Objects which will be hidden for a certain set of frames
          - Provider
        * - number_of_frames
          - The amount of frames this scene has, by default this is bpy.context.scene.frame_end, which is \
            automatically set by the CameraInterface classes. Default: bpy.context.scene.frame_end
          - int
    """

    def __init__(self, config: Config):
        Module.__init__(self, config)

    def run(self):
        """ Hides objects for the set number of frames.
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
