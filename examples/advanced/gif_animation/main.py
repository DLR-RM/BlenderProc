import blenderproc as bproc
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('scene', nargs='?', default="examples/resources/scene.obj", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/gif_animation/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

bproc.init()

# Set a global number of frames for your final animation
frame_end = 99

# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# Set all entities from the scene as solid, passive objects
for obj in objs:
    obj.enable_rigidbody(active=False)

# create an additional item in the scene that is moveable
item = bproc.object.create_primitive("CONE")
item.set_location([0,-1,7])
item.set_rotation_euler([1,0,1])
item.enable_rigidbody(active=True)

# Aktivate the physics simulation
bproc.object.simulate_physics(
    min_simulation_time=4,
    max_simulation_time=20,
    check_object_interval=1
)

# Set how many frames your animation should contain
bproc.utility.set_keyframe_render_interval(frame_end=frame_end)

# define a light and set its location and energy level
light1 = bproc.types.Light()
light1.set_type("POINT")
light1.set_location([5, -5, 5])
light1.set_energy(1000)

# add a second red blinking light source
light2 = bproc.types.Light()
light2.set_type("POINT")
light2.set_color([1,0,0])
light2.set_location([-5,-5,5])

# Define the rythm of the blinking
for frame in range(frame_end):
    # this changes every ten frames from on to off and vice-versa
    if (frame // 10) % 2 == 0:
        light2.set_energy(600, frame=frame)
    else:
        light2.set_energy(0, frame=frame)

# Find point of interest, all cam poses should look towards it
poi = bproc.object.compute_poi(objs)

# define the camera resolution
bproc.camera.set_resolution(512, 512)

# Set time interval from 0 ... 1
time = [t/frame_end for t in range(frame_end)]
# The trajectory of camera positions in [x(t), y(t), z(t)] coordinates
locations = [[(20-10*t)*np.cos(np.pi*(1+0.5*t)), (20-10*t)*np.sin(np.pi*(1+0.5*t)), 8] for t in time]
for frame, location in enumerate(locations):
    # Camera rotation/orientation is chosen such, 
    # that it points towards the scene
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=0)
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    # You have to attach the camera pose to the 
    # already given frames from the physics simulation
    bproc.camera.add_camera_pose(cam2world_matrix, frame=frame)

# activate depth rendering and normals
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.enable_normals_output()
# add segmentation masks (per class and per instance)
bproc.renderer.enable_segmentation_output(map_by=["instance", "name"])

# render the whole pipeline
data = bproc.renderer.render()

# You could additionally write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)

# write the animations into .gif files
bproc.writer.write_gif_animation(args.output_dir, data)

