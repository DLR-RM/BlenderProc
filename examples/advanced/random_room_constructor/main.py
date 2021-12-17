import blenderproc as bproc
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('ikea_path', nargs='?', default="resources/ikea", help="Path to the downloaded IKEA dataset, see the /scripts for the download script")
parser.add_argument('cc_material_path', nargs='?', default="resources/cctextures", help="Path to CCTextures folder, see the /scripts for the download script.")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/random_room_constructor/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# Load materials and objects that can be placed into the room
materials = bproc.loader.load_ccmaterials(args.cc_material_path, ["Bricks", "Wood", "Carpet", "Tile", "Marble"])
interior_objects = []
for i in range(15):
    interior_objects.extend(bproc.loader.load_ikea(args.ikea_path, ["bed", "chair", "desk", "bookshelf"]))

# Construct random room and fill with interior_objects
objects = bproc.constructor.construct_random_room(used_floor_area=25, interior_objects=interior_objects,
                                                  materials=materials, amount_of_extrusions=5)

# Bring light into the room
bproc.lighting.light_surface([obj for obj in objects if obj.get_name() == "Ceiling"], emission_strength=4.0, emission_color=[1,1,1,1])

# Init bvh tree containing all mesh objects
bvh_tree = bproc.object.create_bvh_tree_multi_objects(objects)
floor = [obj for obj in objects if obj.get_name() == "Floor"][0]
poses = 0
tries = 0
while tries < 10000 and poses < 5:
    # Sample point
    location = bproc.sampler.upper_region(floor, min_height=1.5, max_height=1.8)
    # Sample rotation
    rotation = np.random.uniform([1.0, 0, 0], [1.4217, 0, 6.283185307])
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation)

    # Check that obstacles are at least 1 meter away from the camera and make sure the view interesting enough
    if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.2}, bvh_tree) and \
            bproc.camera.scene_coverage_score(cam2world_matrix) > 0.4 and \
            floor.position_is_above_object(location):
        # Persist camera pose
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1

# activate depth rendering
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.set_light_bounces(max_bounces=200, diffuse_bounces=200, glossy_bounces=200, transmission_bounces=200, transparent_max_bounces=200)
# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
