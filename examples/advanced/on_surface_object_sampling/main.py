import blenderproc as bproc
import argparse
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument('camera', nargs='?', default="examples/resources/camera_positions", help="Path to the camera file")
parser.add_argument('scene', nargs='?', default="examples/advanced/on_surface_object_sampling/scene.blend", help="Path to the scene.blend file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/on_surface_object_sampling/output", help="Path to where the final files will be saved ")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
objs = bproc.loader.load_blend(args.scene)

# Retrieve surface and spheres from the list objects
surface = bproc.filter.one_by_attr(objs, "name", "Cube")
spheres = bproc.filter.by_attr(objs, "name", ".*phere.*", regex=True)

# Define a function that samples the pose of a given object
def sample_pose(obj: bproc.types.MeshObject):
    # Sample the spheres location above the surface
    obj.set_location(bproc.sampler.upper_region(
        objects_to_sample_on=[surface],
        min_height=1,
        max_height=4,
        use_ray_trace_check=False
    ))
    obj.set_rotation_euler(np.random.uniform([0, 0, 0], [np.pi * 2, np.pi * 2, np.pi * 2]))

# Sample the spheres on the surface
spheres = bproc.object.sample_poses_on_surface(spheres, surface, sample_pose, min_distance=0.1, max_distance=10)

# Enable physics for spheres (active) and the surface (passive)
for sphere in spheres:
    sphere.enable_rigidbody(True)
surface.enable_rigidbody(False)

# Run the physics simulation
bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=2, max_simulation_time=4, check_object_interval=1)

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

# define the camera intrinsics
bproc.camera.set_resolution(512, 512)

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position, euler_rotation = line[:3], line[3:6]
        matrix_world = bproc.math.build_transformation_mat(position, euler_rotation)
        bproc.camera.add_camera_pose(matrix_world)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
