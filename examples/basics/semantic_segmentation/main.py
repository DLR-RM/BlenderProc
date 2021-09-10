import blenderproc as bproc
from blenderproc.python.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

import argparse

from blenderproc.python.types.LightUtility import Light


parser = argparse.ArgumentParser()
parser.add_argument('camera', nargs='?', default="examples/resources/camera_positions", help="Path to the camera file")
parser.add_argument('scene', nargs='?', default="examples/basics/semantic_segmentation/scene.blend", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/basics/semantic_segmentation/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_blend(args.scene)

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
bproc.camera.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position, euler_rotation = line[:3], line[3:6]
        matrix_world = bproc.math.build_transformation_mat(position, euler_rotation)
        bproc.camera.add_camera_pose(matrix_world)

# activate distance rendering
bproc.renderer.enable_distance_output()
# render the whole pipeline
data = bproc.renderer.render()

# Render segmentation masks (per class and per instance)
data.update(bproc.renderer.render_segmap(map_by=["class", "instance", "name"]))

# Convert distance to depth
data["depth"] = bproc.postprocessing.dist2depth(data["distance"])
del data["distance"]

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
