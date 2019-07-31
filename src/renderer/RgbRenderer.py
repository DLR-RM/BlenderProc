import bpy
import os

from src.renderer.Renderer import Renderer
from src.utility.Utility import Utility


class RgbRenderer(Renderer):

    def __init__(self, config):
        Renderer.__init__(self, config)

    def render_depth(self):
    	output_dir = Utility.resolve_path(self.config.get_string("output_dir"))
    	bpy.context.scene.render.use_compositing = True
    	bpy.context.scene.use_nodes = True
    	bpy.data.scenes["Scene"].render.layers["RenderLayer"].use_pass_z = True
    	tree = bpy.context.scene.node_tree
    	links = tree.links

    	rl = tree.nodes.new('CompositorNodeRLayers')      

    	output_file = tree.nodes.new("CompositorNodeOutputFile")
    	output_file.base_path = os.path.join(output_dir, "depth")
    	output_file.format.file_format = "OPEN_EXR"

    	links.new(rl.outputs[2], output_file.inputs['Image'])


    def run(self):
    	self._configure_renderer()

    	if self.config.get_bool("render_depth"):
    		self.render_depth()

    	self._render("rgb_")
      self._register_output("rgb_", "rgb", ".png")
      