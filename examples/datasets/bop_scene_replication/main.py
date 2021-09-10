import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.utility.Initializer import Initializer
from blenderproc.python.postprocessing.PostProcessingUtility import PostProcessingUtility
from blenderproc.python.types.LightUtility import Light

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('bop_parent_path', nargs='?', help="Path to the bop datasets parent directory")
parser.add_argument('bop_dataset_name', nargs='?', help="Main BOP dataset")
parser.add_argument('bop_toolkit_path', nargs='?', help="Path to bop toolkit")
parser.add_argument('output_dir', nargs='?', default="examples/bop_scene_replication/output", help="Path to where the final files will be saved ")
args = parser.parse_args()

Initializer.init()

# load specified bop objects into the scene
bop_objs = bproc.loader.load_bop(bop_dataset_path = os.path.join(args.bop_parent_path, args.bop_dataset_name),
                          sys_paths = args.bop_toolkit_path,
                          mm2m = True,
                          scene_id = 1,
                          split = 'test') # careful, some BOP datasets only have labeled 'val' sets

# set shading
for j, obj in enumerate(bop_objs):
    obj.set_shading_mode('auto')
        
# Set light source
light_point = Light()
light_point.set_energy(1000)
light_point.set_location([0, 0, -0.8])

# activate distance rendering and set amount of samples for color rendering
bproc.renderer.enable_distance_output()
bproc.renderer.set_samples(50)

# render the cameras of the current scene
data = bproc.renderer.render()

# Write data to bop format
bproc.writer.write_bop(args.output_dir,
                       dataset=args.bop_dataset_name,
                       depths=PostProcessingUtility.dist2depth(data["distance"]),
                       colors=data["colors"],
                       save_world2cam=False) # world coords are arbitrary in most real BOP datasets
