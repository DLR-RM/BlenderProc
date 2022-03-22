import blenderproc as bproc
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('bop_parent_path', nargs='?', help="Path to the bop datasets parent directory")
parser.add_argument('bop_dataset_name', nargs='?', help="Main BOP dataset")
parser.add_argument('output_dir', nargs='?', help="Path to where the final files will be saved ")
args = parser.parse_args()

bproc.init()

# load specified bop objects into the scene
bop_objs = bproc.loader.load_bop_scene(bop_dataset_path = os.path.join(args.bop_parent_path, args.bop_dataset_name),
                          mm2m = True,
                          scene_id = 1,
                          split = 'test') # careful, some BOP datasets only have labeled 'val' sets

# set shading
for j, obj in enumerate(bop_objs):
    obj.set_shading_mode('auto')
        
# Set light source
light_point = bproc.types.Light()
light_point.set_energy(1000)
light_point.set_location([0, 0, -0.8])

# activate depth rendering
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.set_max_amount_of_samples(50)

# render the cameras of the current scene
data = bproc.renderer.render()

# Write data to bop format
bproc.writer.write_bop(os.path.join(args.output_dir, 'bop_data'),
                       dataset=args.bop_dataset_name,
                       depths = data["depth"],
                       colors=data["colors"],
                       save_world2cam=False) # world coords are arbitrary in most real BOP datasets
