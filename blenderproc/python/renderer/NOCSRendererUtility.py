from typing import Optional, Dict, List

import bpy
import numpy as np

from blenderproc.python.material import MaterialLoaderUtility
from blenderproc.python.renderer import RendererUtility
from blenderproc.python.renderer.RendererUtility import set_world_background
from blenderproc.python.types.MaterialUtility import Material
from blenderproc.python.utility.BlenderUtility import get_all_blender_mesh_objects
from blenderproc.python.utility.Utility import Utility, UndoAfterExecution


def render_nocs(output_dir: Optional[str] = None, file_prefix: str = "nocs_", output_key: str = "nocs", return_data: bool = True) -> Dict[str, List[np.ndarray]]:
    """ Renders the Normalized Object Coordinate Space (NOCS).

    Colors each object based on its local coordinates.
    The coordinates [-1, 1] are mapped into the [0, 1] colorspace.
    It is therefore, recommended that all local vertex coordinates are in range [-1, 1].
    The world background is rendered transparent.

    :param output_dir: The directory to write images to. If None is given, the temp dir is used.
    :param file_prefix: The prefix to use for writing the images.
    :param output_key: The key to use for registering the output.
    :param return_data: Whether to load and return generated data.
    :return: A dict containing one entry "nocs" which points to the list of rendered frames.
    """
    if output_dir is None:
        output_dir = Utility.get_temporary_directory()

    with UndoAfterExecution():
        nocs_material = NOCSRendererUtility.create_nocs_material()

        # Set the NOCS material to all objects
        for obj in get_all_blender_mesh_objects():
            if len(obj.material_slots) > 0:
                for i in range(len(obj.material_slots)):
                    obj.data.materials[i] = nocs_material.blender_obj
            else:
                obj.data.materials.append(nocs_material.blender_obj)

        # Make sure the background is black
        set_world_background([0, 0, 0])

        # Set all fast rendering parameters with only one ray per pixel
        RendererUtility._render_init()
        # the amount of samples must be one and there can not be any noise threshold
        RendererUtility.set_max_amount_of_samples(1)
        RendererUtility.set_noise_threshold(0)
        RendererUtility.set_denoiser(None)
        RendererUtility.set_light_bounces(1, 0, 0, 1, 0, 8, 0)
        bpy.context.scene.cycles.filter_width = 0.0

        # Use exr as output format, as it uses a linear colorspace and uses float16
        RendererUtility.set_output_format("OPEN_EXR", 16, enable_transparency=True)
        # Render and ret
        return RendererUtility.render(output_dir, file_prefix, output_key, load_keys={output_key}, return_data=return_data, keys_with_alpha_channel={output_key})


class NOCSRendererUtility:

    @staticmethod
    def create_nocs_material() -> Material:
        """ Creates the material which visualizes the NOCS.

        :return: The created material.
        """
        nocs_material: Material = MaterialLoaderUtility.create("nocs")
        tex_coords_node = nocs_material.new_node("ShaderNodeTexCoord")

        # Scale [-1, 1] to [-0.5, 0.5]
        scale_node = nocs_material.new_node("ShaderNodeVectorMath")
        scale_node.operation = "SCALE"
        scale_node.inputs[3].default_value = 0.5

        # Move [-0.5, 0.5] to [0, 1]
        add_node = nocs_material.new_node("ShaderNodeVectorMath")
        add_node.operation = "ADD"
        add_node.inputs[1].default_value = [0.5, 0.5, 0.5]

        # Link the three nodes
        nocs_material.link(tex_coords_node.outputs["Object"], scale_node.inputs[0])
        nocs_material.link(scale_node.outputs["Vector"], add_node.inputs[0])

        # Link to output node
        output_node = nocs_material.get_the_one_node_with_type('OutputMaterial')
        nocs_material.link(add_node.outputs["Vector"], output_node.inputs['Surface'])
        return nocs_material
