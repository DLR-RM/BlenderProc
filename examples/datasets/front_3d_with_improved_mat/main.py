import blenderproc as bproc
import argparse
import os
import numpy as np
import random
import time
import bpy
import bpy_extras
import mathutils

parser = argparse.ArgumentParser()
parser.add_argument("front", help="Path to the 3D front file")
parser.add_argument("future_folder", help="Path to the 3D Future Model folder.")
parser.add_argument("front_3D_texture_path", help="Path to the 3D FRONT texture folder.")
parser.add_argument('cc_material_path', nargs='?', default="resources/cctextures", help="Path to CCTextures folder, see the /scripts for the download script.")
parser.add_argument("output_dir", nargs='?', default="examples/datasets/front_3d_with_improved_mat/output", help="Path to where the data should be saved")
args = parser.parse_args()

if not os.path.exists(args.front) or not os.path.exists(args.future_folder):
    raise Exception("One of the two folders does not exist!")

bproc.init()
mapping_file = bproc.utility.resolve_resource(os.path.join("front_3D", "3D_front_mapping.csv"))
mapping = bproc.utility.LabelIdMapping.from_csv(mapping_file)

# set the light bounces
bproc.renderer.set_light_bounces(diffuse_bounces=200, glossy_bounces=200, max_bounces=200,
                                  transmission_bounces=200, transparent_max_bounces=200)

# load the front 3D objects
loaded_objects = bproc.loader.load_front3d(
    json_path=args.front,
    future_model_path=args.future_folder,
    front_3D_texture_path=args.front_3D_texture_path,
    label_mapping=mapping
)

cc_materials = bproc.loader.load_ccmaterials(args.cc_material_path, ["Bricks", "Wood", "Carpet", "Tile", "Marble"])

floors = bproc.filter.by_attr(loaded_objects, "name", "Floor.*", regex=True)
for floor in floors:
    # For each material of the object
    for i in range(len(floor.get_materials())):
        # In 95% of all cases
        if np.random.uniform(0, 1) <= 0.95:
            # Replace the material with a random one
            floor.set_material(i, random.choice(cc_materials))


baseboards_and_doors = bproc.filter.by_attr(loaded_objects, "name", "Baseboard.*|Door.*", regex=True)
wood_floor_materials = bproc.filter.by_cp(cc_materials, "asset_name", "WoodFloor.*", regex=True)
for obj in baseboards_and_doors:
    # For each material of the object
    for i in range(len(obj.get_materials())):
        # Replace the material with a random one
        obj.set_material(i, random.choice(wood_floor_materials))


walls = bproc.filter.by_attr(loaded_objects, "name", "Wall.*", regex=True)
marble_materials = bproc.filter.by_cp(cc_materials, "asset_name", "Marble.*", regex=True)
for wall in walls:
    # For each material of the object
    for i in range(len(wall.get_materials())):
        # In 50% of all cases
        if np.random.uniform(0, 1) <= 0.1:
            # Replace the material with a random one
            wall.set_material(i, random.choice(marble_materials))

# Init sampler for sampling locations inside the loaded front3D house
point_sampler = bproc.sampler.Front3DPointInRoomSampler(loaded_objects)

# Init bvh tree containing all mesh objects
bvh_tree = bproc.object.create_bvh_tree_multi_objects([o for o in loaded_objects if isinstance(o, bproc.types.MeshObject)])

poses = 0
tries = 0

def check_name(name):
    for category_name in ["chair", "sofa", "table", "bed"]:
        if category_name in name.lower():
            return True
    return False

# filter some objects from the loaded objects, which are later used in calculating an interesting score
special_objects = [obj.get_cp("category_id") for obj in loaded_objects if check_name(obj.get_name())]

proximity_checks = {"min": 0.5, "no_background": False}

shapenet_objs_1 = []
shapenet_dir = "/media/domin/data/shapenet/ShapeNetCore.v2/"
s = 0
while s < 10:
    cat_id = random.choice(os.listdir(shapenet_dir))
    if cat_id.isdigit():
        shapenet_objs_1.append(bproc.loader.load_shapenet(shapenet_dir, cat_id, move_object_origin=False))
        s += 1

shapenet_objs_2 = [obj.duplicate() for obj in shapenet_objs_1]

for shapenet_objs in [shapenet_objs_1, shapenet_objs_2]:
    for obj in shapenet_objs:
        location = point_sampler.sample(np.random.uniform(0, 1.8))
        obj.set_location(location)
        obj.set_rotation_euler(bproc.sampler.uniformSO3())
        obj.set_scale(np.random.uniform([0.5, 0.5, 0.5], [2, 2, 2]))


bop_bvh_all1 = bproc.object.create_bvh_tree_multi_objects(loaded_objects + shapenet_objs_1)
bop_bvh_all2 = bproc.object.create_bvh_tree_multi_objects(loaded_objects + shapenet_objs_2)
pairs = 0

cam_poses1 = []
cam_poses2 = []
while pairs < 1:

    begin2 = time.time()
    target_obj = None
    random.shuffle(loaded_objects)
    for obj in loaded_objects:
        if obj.has_cp("type") and obj.get_cp("type") == "Object":
            target_obj = obj
            break

    bop_bvh_target = bproc.object.create_bvh_tree_multi_objects([target_obj])
    #bop_bvh_obstacle = bproc.object.create_bvh_tree_multi_objects([obj for obj in loaded_objects if obj != target_obj])

    print(target_obj.get_name())
    print("a", time.time() - begin2)
    begin2 = time.time()


    cam_poses = []
    last_frame_hit_points = None
    for p in range(2):
        bop_bvh_all = bop_bvh_all1 if p == 0 else bop_bvh_all2
        for tries in range(1000):
            begin = time.time()
            # Sample point inside house
            height = np.random.uniform(0, 1.8)
            location = point_sampler.sample(height)
            # Sample rotation (fix around X and Y axis)
            rotation = np.random.uniform([np.pi / 4, -np.pi / 4, 0], [np.pi / 4 * 3, np.pi / 4, np.pi * 2])
            cam2world_matrix = bproc.math.build_transformation_mat(location, rotation)
            #print("1", time.time() - begin)

            # Check that obstacles are at least 1 meter away from the camera and have an average distance between 2.5 and 3.5
            # meters and make sure that no background is visible, finally make sure the view is interesting enough
            begin = time.time()
            area, hit_points = bproc.camera.objects_area(cam2world_matrix, bop_bvh_target, bop_bvh_all, sqrt_number_of_rays=10)
            
            #print("2", time.time() - begin)
            #print(tries, area)
            #print(area)
            if area > 0.1:
                if last_frame_hit_points is not None:
                    begin = time.time()
                    both_visible_points = []
                    for points, campose in [(last_frame_hit_points, cam2world_matrix), (hit_points, cam_poses[-1])]:
                        position = cam2world_matrix[:3, 3]
                        for point in last_frame_hit_points:
                            _, _, _, dist = bop_bvh_all.ray_cast(position, point - position)
                            if abs(dist - np.linalg.norm(position - point)) < 1e-4:
                                both_visible_points.append(point)
                    #print("3a", time.time() - begin)
                                
                    if len(both_visible_points) == 0:
                        continue

                    begin = time.time()
                    both_visible_points = np.array(both_visible_points)
                    both_visible_points = np.concatenate((both_visible_points, np.ones_like(both_visible_points[:,:1])), -1)
                    K = bproc.camera.get_intrinsics_as_K_matrix()
                    K[1][2] = (bpy.context.scene.render.resolution_x - 1) - K[1][2]

                    points_2d = []
                    for campose in [cam2world_matrix, cam_poses[-1]]:
                        local_point_clouds = np.matmul(np.linalg.inv(campose), both_visible_points.T).T
                        local_point_clouds[..., 2] *= -1
                        # Reproject 3d point

                        point_2d = np.matmul(K, local_point_clouds[..., :3].T).T
                        point_2d /= point_2d[..., 2:]
                        point_2d = point_2d[..., :2]

                        point_2d[..., 1] = (bpy.context.scene.render.resolution_x - 1) - point_2d[..., 1]

                        point_2d[(point_2d < -0.5 - 1e-3).any(-1)] = np.nan
                        point_2d[(point_2d > (bpy.context.scene.render.resolution_x - 1 + 0.5) + 1e-3).any(-1)] = np.nan
                        points_2d.append(point_2d)
                        """print(point_2d)
                        for point in both_visible_points:
                            bpy.context.scene.camera.matrix_world = mathutils.Matrix(campose)
                            print(bpy_extras.object_utils.world_to_camera_view(bpy.context.scene, bpy.context.scene.camera, mathutils.Vector(point[:3])))

                        print(campose, bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
                        print(both_visible_points)
                        sdfsdf"""
                    points_2d = np.transpose(np.array(points_2d), [1, 0, 2])
                    mask = np.isnan(points_2d).any(-1).any(-1)
                    #print(points_2d.shape, mask.shape)
                    points_2d = points_2d[~mask]
                    #print("3b", time.time() - begin)
                    if len(points_2d) == 0:
                        continue
                    area1 = np.prod(points_2d[:, 0].max(0) - points_2d[:, 0].min(0)) / (bpy.context.scene.render.resolution_x * bpy.context.scene.render.resolution_y)
                    area2 = np.prod(points_2d[:, 1].max(0) - points_2d[:, 1].min(0)) / (bpy.context.scene.render.resolution_x * bpy.context.scene.render.resolution_y)
                    print(area1, area2)
                    if min(area1, area2) < 0.1:
                        continue

                    """import matplotlib.pyplot as plt
                    plt.figure()
                    plt.scatter(points_2d[:, 0,0], points_2d[:, 0,1])
                    plt.scatter(points_2d[:, 1,0], points_2d[:, 1,1])
                    plt.xlim(0, 512)
                    plt.ylim(0, 512)
                    plt.savefig("scatter.png")
"""
                #if bproc.camera.scene_coverage_score(cam2world_matrix, special_objects, special_objects_weight=10.0) > 0.8 \
                #        and bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, proximity_checks, bvh_tree):
                cam_poses.append(cam2world_matrix)
                last_frame_hit_points = hit_points
                break


    print("b", time.time() - begin2)

    if len(cam_poses) == 2:
        pairs += 1
        cam_poses1.append(cam_poses[0])
        cam_poses2.append(cam_poses[1])
        #for cam_pose in cam_poses:
        #    bproc.camera.add_camera_pose(cam_pose)


for obj in shapenet_objs_1:
    obj.hide(False)
for obj in shapenet_objs_2:
    obj.hide(True)

for cam_pose in cam_poses1:
    bproc.camera.add_camera_pose(cam_pose)

data= {}
data["colors1"] = bproc.renderer.render()["colors"]


for obj in shapenet_objs_1:
    obj.hide(True)
for obj in shapenet_objs_2:
    obj.hide(False)

bproc.utility.reset_keyframes()
for cam_pose in cam_poses2:
    bproc.camera.add_camera_pose(cam_pose)
data["colors2"] = bproc.renderer.render()["colors"]

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)