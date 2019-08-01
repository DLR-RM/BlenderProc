import bpy
import os

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility


class RgbRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config)

    def render_depth(self):
    	bpy.context.scene.render.use_compositing = True
    	bpy.context.scene.use_nodes = True
    	bpy.data.scenes["Scene"].render.layers["RenderLayer"].use_pass_z = True
    	tree = bpy.context.scene.node_tree
    	links = tree.links

    	# Create a render layer
    	rl = tree.nodes.new('CompositorNodeRLayers')      

    	output_file = tree.nodes.new("CompositorNodeOutputFile")
    	output_file.base_path = os.path.join(self.output_dir, "depth")
    	output_file.format.file_format = "OPEN_EXR"

    	# Feed the Z output of the render layer to the input of the file IO layer
    	links.new(rl.outputs[2], output_file.inputs['Image'])


    def run(self):
    	self._configure_renderer()

    	if self.config.get_bool("render_depth"):
    		self.render_depth()

    	bpy.context.scene.render.image_settings.color_mode = "RGB"
    	bpy.context.scene.render.image_settings.file_format = "PNG"
    	bpy.context.scene.render.image_settings.color_depth = "8"

    	self._render("rgb_")
    	self._register_output("rgb_", "rgb", ".png")
      