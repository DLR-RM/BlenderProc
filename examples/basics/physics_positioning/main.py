import blenderproc as bproc
import argparse
import numpy as np
import bpy
import os
import random
import time
"""
  this py , load obj and duplicate them .Then set them particapte in physical simulation
  ground objs as obstacle
  the obj set in the sky, then fall into the boxes,maybe they fall out

"""

parser = argparse.ArgumentParser()
parser.add_argument('spheres_obj', nargs='?', default="examples/basics/physics_positioning/active.obj",
                    help="Path to the object file with sphere objects")
parser.add_argument('ground_obj', nargs='?', default="examples/basics/physics_positioning/passive.obj",
                    help="Path to the object file with the ground object")
parser.add_argument('output_dir', nargs='?', default="examples/basics/physics_positioning/output",
                    help="Path to where the final files, will be saved")
args = parser.parse_args()

start_time = time.time()

bproc.init()
# active and passive objects into the scene
object_list = []
object_number = 1
for i in range(object_number):
    object_list.append(bproc.loader.load_obj(args.spheres_obj)[0])

ground = bproc.loader.load_obj(args.ground_obj)

# Create mylight and set it's properties
"""area1 = bproc.types.Light()
area1.set_type("AREA")
area1.set_location([-0.473, 1.2443, 1.0613])
area1.set_rotation_euler([-0.8919, -0.2740, 0.2356])
area1.set_energy(10)
area1.set_color([1, 1, 1])
area1.set_scale([5, 5, 5])

# top light
area2 = bproc.types.Light()
area2.set_type("AREA")
area2.set_location([0, 0, 3])
area2.set_rotation_euler([0, 0, 0])
area2.set_energy(10)
area2.set_color([1, 1, 1])
area2.set_scale([5, 5, 5])"""

# set category_id to every objects in case something gose wrong!
id = 1
for obj in bpy.data.objects:
    bproc.types.MeshObject(obj).set_cp("category_id", id)
    id += 1


# set camera_location and put the direction of the camera lens
left = np.linspace(-0.4, -0.01, 10000)
right = np.linspace(0.01, 0.4, 10000)
high = np.linspace(0.5, 0.9, 10000)
xyz_random = {'0': left, '1': right}
x = random.randint(0, 1)  # create one random number in 0 or 1
y = random.randint(0, 1)
# choose random number in list
choose_x = random.sample(list(xyz_random[str(x)]), 1)[0]
choose_y = random.sample(list(xyz_random[str(y)]), 1)[0]
choose_z = random.sample(list(high), 1)[0]

shuju = np.array([0, 0, 1, 0.03979351, 0, 0], dtype=np.float)
shuju = np.array([0, 0, 0.68, 0, 0, 0], dtype=np.float)
shuju = np.array([0.43, -0.22, 0.68, 0, 0, 0], dtype=np.float)
shuju = np.array([choose_x, choose_y, choose_z, 0, 0, 0], dtype=np.float)
camera_position, camera_rotation = shuju[:3], shuju[3: 6]

# set the obstacle status and make try to make them right,it is planer
# ground1 = bproc.filter.one_by_attr(ground, "name", "buttom_plane")
# ground1.enable_rigidbody(active=False, collision_shape="CONVEX_HULL", friction=1, mass=1)
# ground1.enable_rigidbody(active=False, collision_shape="BOX", friction=1)
ground2 = ground[0]  # bproc.filter.one_by_attr(ground, "name", "Cube")
# ground2.set_scale([0.24, 0.21, 0.27])
"""ground2.enable_rigidbody(active=False, collision_shape="MESH", friction=1, mass=1)"""
# set the target object enbidy activate
for obj in object_list:
    obj.enable_rigidbody(active=True, collision_shape="BOX", friction=1, mass=1)

print("normals")
# activate normal rendering
bproc.renderer.enable_normals_output()
bproc.renderer.set_max_amount_of_samples(1)

NUM_RUMs = 360*3
for r in range(100):
    print("reset")
    bproc.utility.reset_keyframes()

    # set resolution
    """image_width = 640
    image_height = 480
    bproc.camera.set_resolution(image_width, image_height)"""

    """# set K matrix, camera
    fx = 609.4411010742188
    fy = 607.9595336914062
    cx = 321.0838928222656
    cy = 238.0767059326172
    # fx, fy, cx, cy = 1, 1, 0, 0
    K = np.array([
        [fx, 0, cx],
        [0, fy, cy],
        [0, 0, 1]
    ])
    # fx, fy, cx, cy = 1, 1, 0, 0
    bproc.camera.set_intrinsics_from_K_matrix(K, image_width, image_height)"""

    print("cam add")
    cam_poi = [0, 0, 0]  # camera_lens_target
    rotation_matrixrotation_matrix = bproc.camera.rotation_from_forward_vec(cam_poi - camera_position)
    cam2world_matrix = bproc.math.build_transformation_mat(camera_position, rotation_matrixrotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)
    # bpy.data.objects['Camera'].select_set(1)  # set the Field of View
    ##bpy.context.object.data.angle = 1.08616
    # bpy.context.object.data.angle = 0.6
    #bpy.data.cameras['Camera'].angle = 1.23919
    # set world_color
    #bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.749253, 0.749253, 1)
    # bpy.ops.image.open(filepath="//..\\christmas_photo_studio_03_4k.exr", directory="C:\\Users\\Administrator\\Desktop\\", files=[{"name":"christmas_photo_studio_03_4k.exr", "name":"christmas_photo_studio_03_4k.exr"}], relative_path=True, show_multiview=False)
    # s = 'D:/BLENDER_PRO/BlenderProc-main/examples/basics/physics_positioning/christmas_photo_studio_03_4k.exr'
    s = 'D:/BLENDER_PRO/BlenderProc-main/examples/basics/physics_positioning/autoshop_01_4k.exr'

    # random set hdr
    # get hdr_path
    """hdr_path = os.path.abspath(os.path.join(os.getcwd(), "hello", "scene_model", "hdr"))
    hdr_list = os.listdir(hdr_path)
    num_hdr_list = len(hdr_list)
    rand_seed = np.random.randint(0, num_hdr_list)
    real_hdr_path = os.path.join(hdr_path, hdr_list[rand_seed])
    # random set hdr
    hdr_path = os.path.abspath(os.path.join(os.getcwd(), "hello", "scene_model", "hdr", "autoshop_01_4k.exr"))
    # s = 'examples/basics/physics_positioning/autoshop_01_4k.exr'
    #bproc.world.set_world_background_hdr_img(real_hdr_path)"""


    # load _world_hrd
    # bproc.loader.get_random_world_background_hdr_img_path_from_haven()

    ## Define a function that samples the pose of ground to location[0, 0, 0]
    """def sample_pose(obj: bproc.types.MeshObject):
        obj.set_location([0, 0, 0])
        obj.set_rotation_euler(bproc.sampler.uniformSO3())  # this generate z rotation only,maybe
        obj.set_rotation_euler([0, 0, 0])


    ## Define a function that samples the pose of objects which should be activate,put them in the sky
    def sample_pose_sky(obj: bproc.types.MeshObject):
        #    obj.set_location(np.random.uniform([-5, -5, 8], [5, 5, 12]))
        obj.set_location(np.random.uniform([-0.24, -0.2, 0.4], [0.24, 0.2, 1.8]))
        obj.set_rotation_euler(bproc.sampler.uniformSO3())


    # bpy.context.object.data.angle = 1.10824

    ## Sample the poses of all ground above the ground without any collisions in-between
    # bproc.object.sample_poses(
    #    ground,  # put list in it
    #    sample_pose_func=sample_pose  # call sample_pose to ground
    # )

    # test sample the pose of all spheres
    bproc.object.sample_poses(
        object_list,  # put list in it
        sample_pose_func=sample_pose_sky,  # call sample_pose to ground
        objects_to_check_collisions=object_list
    )"""


    for k in range(2000):
        print("physics")
        # do pyhsics simulation
        bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=1, max_simulation_time=20,
                                                          check_object_interval=0.1)

        #
        # # activate depth rendering
        # bproc.renderer.enable_depth_output(activate_antialiasing=False)


        # render the whole pipeline
        print("iteration ", k)
        print("render rgb")
        data = bproc.renderer.render()
        seg_data = bproc.renderer.render_segmap(map_by=["instance", "class", "name"])
    exit(0)

    print("next")
    # Write data to coco file
    """bproc.writer.write_coco_annotations(os.path.join(args.output_dir, 'coco_data'),
                            instance_segmaps=seg_data["instance_segmaps"],
                            instance_attribute_maps=seg_data["instance_attribute_maps"],
                            colors=data["colors"],
                            color_file_format="JPEG")"""
end_time = time.time()
TIME = end_time - start_time
print("end_success")
print("in total spend {} seconds".format(TIME))
