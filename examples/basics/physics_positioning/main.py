import blenderproc as bproc
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('spheres_obj', nargs='?', default="examples/basics/physics_positioning/active.obj", help="Path to the object file with sphere objects")
parser.add_argument('ground_obj', nargs='?', default="examples/basics/physics_positioning/passive.obj", help="Path to the object file with the ground object")
parser.add_argument('output_dir', nargs='?', default="examples/basics/physics_positioning/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# Load active and passive objects into the scene
spheres = bproc.loader.load_obj(args.spheres_obj)
ground = bproc.loader.load_obj(args.ground_obj)[0]

# Create a SUN light and set its properties
light = bproc.types.Light()
light.set_type("SUN")
light.set_location([0, 0, 0])
light.set_rotation_euler([-0.063, 0.6177, -0.1985])
light.set_energy(1)
light.set_color([1, 0.978, 0.407])

# Add a camera pose via location + euler angles
bproc.camera.add_camera_pose(bproc.math.build_transformation_mat([0, -47.93, 16.59], [1.3, 0, 0]))

# Define a function that samples the pose of a given sphere
def sample_pose(obj: bproc.types.MeshObject):
    obj.set_location(np.random.uniform([-5, -5, 8], [5, 5, 12]))
    obj.set_rotation_euler(bproc.sampler.uniformSO3())

# Sample the poses of all spheres above the ground without any collisions in-between
bproc.object.sample_poses(
    spheres,
    sample_pose_func=sample_pose
)

# Make all spheres actively participate in the simulation
for obj in spheres:
    obj.enable_rigidbody(active=True)
# The ground should only act as an obstacle and is therefore marked passive.
# To let the spheres fall into the valleys of the ground, make the collision shape MESH instead of CONVEX_HULL.
ground.enable_rigidbody(active=False, collision_shape="MESH")

# Run the simulation and fix the poses of the spheres at the end
bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=4, max_simulation_time=20, check_object_interval=1)

# render the whole pipeline
data = bproc.renderer.render()

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
