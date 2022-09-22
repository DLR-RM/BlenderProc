import blenderproc as bproc
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('camera', help="Path to the camera file which describes one camera pose per line, here the output of scn2cam from the SUNCGToolbox can be used")
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/suncg_basic/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
objs = bproc.loader.load_suncg(args.house, label_mapping=label_mapping)

# define the camera intrinsics
bproc.camera.set_resolution(512, 512)

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position = bproc.math.change_coordinate_frame_of_point(line[:3], ["X", "-Z", "Y"])
        rotation = bproc.math.change_coordinate_frame_of_point(line[3:6], ["X", "-Z", "Y"])
        matrix_world = bproc.math.build_transformation_mat(position, bproc.camera.rotation_from_forward_vec(rotation))
        bproc.camera.add_camera_pose(matrix_world)

# makes Suncg objects emit light
bproc.lighting.light_suncg_scene()

# activate normal and depth rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.material.add_alpha_channel_to_textures(blurry_edges=True)
bproc.renderer.enable_segmentation_output(map_by=["category_id"])

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
