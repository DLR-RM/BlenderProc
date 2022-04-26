import blenderproc as bproc
from pathlib import Path

from blenderproc.python.utility.MathUtility import change_source_coordinate_frame_of_transformation_matrix
import argparse
import os
import numpy as np
import random
import time
import bpy
import bpy_extras
import mathutils

parser = argparse.ArgumentParser()
parser.add_argument('hdri_path', nargs='?', default="resources/haven", help="The folder where the `hdri` folder can be found, to load an world environment")
parser.add_argument('cc_material_path', nargs='?', default="resources/cctextures", help="Path to CCTextures folder, see the /scripts for the download script.")
parser.add_argument("output_dir", nargs='?', default="examples/datasets/front_3d_with_improved_mat/output", help="Path to where the data should be saved")
args = parser.parse_args()


bproc.init()
bproc.camera.set_resolution(128, 128)
mapping_file = bproc.utility.resolve_resource(os.path.join("front_3D", "3D_front_mapping.csv"))
mapping = bproc.utility.LabelIdMapping.from_csv(mapping_file)

# set the light bounces
bproc.renderer.set_light_bounces(diffuse_bounces=200, glossy_bounces=200, max_bounces=200,
                                  transmission_bounces=200, transparent_max_bounces=200)


cc_materials = bproc.loader.load_ccmaterials(args.cc_material_path, preload=True)

plane = bproc.object.create_primitive("PLANE")
plane.set_location([0, 0, 0])
plane.set_scale([1000, 1000, 100])


poses = 0
tries = 0

delta_poses = np.load("/media/domin/data/image_matching_challenge/delta_poses.npy")

proximity_checks = {"min": 0.5, "no_background": False}

"""shapenet_objs_1 = []
shapenet_dir = "/media/domin/data/shapenet/ShapeNetCore.v2/"
s = 0
while s < 50:
    cat_id = random.choice(os.listdir(shapenet_dir))
    if cat_id.isdigit():
        shapenet_objs_1.append(bproc.loader.load_shapenet(shapenet_dir, cat_id, move_object_origin=False))
        s += 1"""
shapenet_objs_1 = bproc.loader.load_blend("/media/domin/data/image_matching_challenge/shapenet100.blend")

#for obj in shapenet_objs_1[:]:
#    shapenet_objs_1.append(obj.duplicate())

shapenet_objs_2 = [obj.duplicate() for obj in shapenet_objs_1]


begin2 = time.time()
target_obj = random.choice(shapenet_objs_1)

for shapenet_objs in [shapenet_objs_1, shapenet_objs_2]:
    for obj in shapenet_objs:
        if target_obj != obj:
            small = np.random.rand() > 0.3
            if not small:
                location = np.random.uniform((-150, -100, 0), (150, 150, 0))
            else:
                location = np.random.uniform((-50, -50, 0), (50, 0, 0))

            obj.set_location(location)
            obj.set_rotation_euler( mathutils.Matrix.Rotation(np.random.uniform(0, 360), 3, 'Z').to_euler())
            max_size = 10 if np.logical_and(np.array([-100, -100]) < location[:2], np.array([100, 0]) > location[:2]).all() else 100
            obj.set_scale(np.random.uniform([0.5, 0.5, 0.5], [max_size, max_size, max_size]))
            obj.set_location([location[0],location[1],-obj.get_bound_box()[:,2].min()])
#bvh_obstacle = bproc.object.create_bvh_tree_multi_objects([obj for obj in loaded_objects if obj != target_obj])

target_obj.set_scale(np.random.uniform([5, 5, 5], [100, 100, 100]))
target_obj.set_location([0,-target_obj.get_bound_box()[:,1].min(),-target_obj.get_bound_box()[:,2].min()])

bvh_target = bproc.object.create_bvh_tree_multi_objects([target_obj])
bvh_all1 = bproc.object.create_bvh_tree_multi_objects(shapenet_objs_1 + [plane])
bvh_all2 = bproc.object.create_bvh_tree_multi_objects(shapenet_objs_2 + [target_obj, plane])

print(target_obj.get_name())
print("a", time.time() - begin2)

pairs = 0

cam_poses1 = []
visible_objects = set()
cam_poses2 = []
while pairs <5:
    
    for outer_tries in range(10):
        cam_poses = []
        last_frame_hit_points = None
        for p in range(2):
            bvh_all = bvh_all1 if p == 0 else bvh_all2
            for tries in range(1000):
                begin = time.time()
                # Sample point inside house
                if p == 0 or True:
                    #height = np.random.uniform(0, 1.8)
                    location = np.random.uniform((-100, -100, 0), (100, 0, 2))
                    # Sample rotation (fix around X and Y axis)
                    rotation = mathutils.Matrix.Rotation(np.random.uniform(0, 360), 3, 'Z') @ mathutils.Matrix.Rotation(np.random.normal(91.79, 13.46) / 180 * np.pi, 3, 'X') @ mathutils.Matrix.Rotation(np.random.normal(0, 8.0) / 180 * np.pi, 3, 'Z')# np.random.uniform([np.pi / 4, -np.pi / 4, 0], [np.pi / 4 * 3, np.pi / 4, np.pi * 2])
                    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation)
                    #print("1", time.time() - begin)
                else:
                    delta_pose = random.choice(delta_poses)
                    delta_pose = change_source_coordinate_frame_of_transformation_matrix(delta_pose, ["X", "-Y", "-Z"])
                    transl = bproc.sampler.sphere([0,0,0], np.random.uniform(0.1, 1), "SURFACE")
                    tmat = np.identity(4)
                    tmat[:3,:3] = delta_pose[:3,:3]
                    tmat[:3,3] = transl
                    cam2world_matrix = cam_poses[-1] @ tmat
                    cam2world_matrix[:3,3] = np.random.uniform((-100, 0, 0), (100, -100, 2))
                    #print(cam2world_matrix, tmat)
                    #bpy.context.scene.camera.matrix_world = mathutils.Matrix(cam2world_matrix)
                    #sdfs

                # Check that obstacles are at least 1 meter away from the camera and have an average distance between 2.5 and 3.5
                # meters and make sure that no background is visible, finally make sure the view is interesting enough
                begin = time.time()
                area, hit_points = bproc.camera.objects_area(cam2world_matrix, bvh_target, bvh_all, sqrt_number_of_rays=10)
                
                #print("2", time.time() - begin)
                #print(tries, area)
                #print(area)
                if area > 0.1:
                    if last_frame_hit_points is not None:
                        begin = time.time()
                        both_visible_points = []
                        for points, campose in [(last_frame_hit_points, cam2world_matrix), (hit_points, cam_poses[-1])]:
                            position = campose[:3, 3]
                            for point in points:
                                _, _, _, dist = bvh_all.ray_cast(position, point - position)
                                #print(dist, abs(dist - np.linalg.norm(position - point)) if dist is not None else None, point, position)
                                if dist is not None and abs(dist - np.linalg.norm(position - point)) < 1e-4:
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
            visible_objects.update(bproc.camera.visible_objects(cam_poses[0]))
            visible_objects.update(bproc.camera.visible_objects(cam_poses[1]))
            pc1 = bproc.camera.compute_point_cloud(cam_poses[0], bvh_target, bvh_all1)
            pc2 = bproc.camera.compute_point_cloud(cam_poses[1], bvh_target, bvh_all1)
            pcs = np.stack((pc1, pc2), 0)

            cam_extrinsics = []
            for cam_pose in cam_poses:
                bproc.camera.add_camera_pose(cam_pose)
                cam_extrinsics.append((np.linalg.inv(cam_poses[1]), cam_poses[1][:3, 3]))

            matches = bproc.camera.compute_matches(pcs, cam_extrinsics)
            print(matches.shape)

            """print("spheres")
            for point in pc1.reshape(-1, 3)[::10]:
                if not np.isnan(point).any():
                    sphere = bproc.object.create_primitive("SPHERE")
                    sphere.set_scale([0.01, 0.01, 0.01])
                    sphere.set_location(point)"""
            sdfsd

            break

print(visible_objects)
for obj in visible_objects:
    if np.random.rand() > 0.75:
        if len(obj.get_materials()) == 0:
            material = random.choice(cc_materials)
            print(obj.get_name(), material.get_name())
            obj.add_material(material)
        else:
            for i in range(len(obj.get_materials())):
                material = random.choice(cc_materials)
                print(obj.get_name(),  material.get_name())
                obj.set_material(i, material)


floor_materials = bproc.filter.by_cp(cc_materials, "asset_name", "Concrete.*|Ground.*|Gravel.*|PavingStones.*|Asphalt.*", regex=True)
mat = random.choice(floor_materials)
print("Floor", mat.get_name())
plane.add_material(mat)
plane.scale_uv_coordinates(np.random.uniform(900, 1200))

bproc.loader.load_ccmaterials(args.cc_material_path, fill_used_empty_materials=True)



lights = []
for i in range(np.random.randint(0, 20)):
    light = bproc.types.Light()
    light_type = "AREA" if np.random.rand() > 0.5 else "POINT"
    light.set_type(light_type)
    light.set_location(np.random.uniform((-100, -100, 0), (100, 50, 10)))
    if light_type == "AREA":
        light.set_energy(np.random.randint(100, 2000))
        light.blender_obj.data.size = 5
    else:
        light.set_energy(np.random.randint(1000, 20000))
    lights.append(light)
def randomize():
    haven_hdri_path = bproc.loader.get_random_world_background_hdr_img_path_from_haven(args.hdri_path)
    bproc.world.set_world_background_hdr_img(haven_hdri_path)

    if np.random.rand() > 0.75:
        bproc.camera.add_depth_of_field(None, np.random.uniform(2.5, 10), focal_distance= np.random.uniform(5, 100))
    else:
        bproc.camera.remove_depth_of_field()

    if np.random.rand() > 0.5:
        bpy.context.scene.cycles.film_exposure = np.random.uniform(0.5, 5)
    else:
        bpy.context.scene.cycles.film_exposure = 1


    if np.random.rand() > 0.5:
        bpy.context.scene.view_settings.look = np.random.choice(["Low Contrast" ,"Medium High Contrast" , "Medium Contrast", "Medium Low Contrast", "High Contrast"])
    else:
        bpy.context.scene.view_settings.look = "None"

    if np.random.rand() > 0.75:
        bpy.context.scene.view_settings.gamma = np.random.uniform(0.5, 2)
    else:
        bpy.context.scene.view_settings.gamma = 1

    if np.random.rand() > 0.75:
        plane.set_material(0, random.choice(floor_materials))

        bproc.loader.load_ccmaterials(args.cc_material_path, fill_used_empty_materials=True)


bproc.renderer.set_max_amount_of_samples(64)
bproc.utility.reset_keyframes()

randomize()

for obj in shapenet_objs_1:
    obj.hide(False)
for obj in shapenet_objs_2:
    obj.hide(True)


for cam_pose in cam_poses1:
    bproc.camera.add_camera_pose(cam_pose)

data= {}
data["colors1"] = bproc.renderer.render()["colors"]

randomize()

for obj in shapenet_objs_1:
    obj.hide(True)
for obj in shapenet_objs_2:
    obj.hide(False)
target_obj.hide(False)

for light in lights:
    light.set_location(np.random.uniform((-100, -100, 0), (100, 50, 10)))

bproc.utility.reset_keyframes()
for cam_pose in cam_poses2:
    bproc.camera.add_camera_pose(cam_pose)
data["colors2"] = bproc.renderer.render()["colors"]

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)