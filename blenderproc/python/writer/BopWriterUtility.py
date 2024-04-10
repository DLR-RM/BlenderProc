"""Allows rendering the content of the scene in the bop file format."""

from functools import partial
import json
from multiprocessing import Pool
import os
import glob
import trimesh
from typing import List, Optional, Dict, Tuple
import warnings
import datetime

import numpy as np
import png
import cv2
import bpy
from mathutils import Matrix
import sys

from blenderproc.python.types.MeshObjectUtility import MeshObject, get_all_mesh_objects
from blenderproc.python.writer.WriterUtility import _WriterUtility
from blenderproc.python.types.LinkUtility import Link
from blenderproc.python.utility.SetupUtility import SetupUtility
from blenderproc.python.utility.MathUtility import change_target_coordinate_frame_of_transformation_matrix

# EGL is not available under windows
if sys.platform in ["linux", "linux2"]:
    os.environ['PYOPENGL_PLATFORM'] = 'egl'


def write_bop(output_dir: str, target_objects: Optional[List[MeshObject]] = None,
              depths: List[np.ndarray] = None, colors: List[np.ndarray] = None,
              color_file_format: str = "PNG", dataset: str = "", append_to_existing_output: bool = True,
              depth_scale: float = 1.0, jpg_quality: int = 95, save_world2cam: bool = True,
              ignore_dist_thres: float = 100., m2mm: Optional[bool] = None, annotation_unit: str = 'mm',
              frames_per_chunk: int = 1000, calc_mask_info_coco: bool = True, delta: float = 0.015,
              num_worker: Optional[int] = None):
    """Write the BOP data

    :param output_dir: Path to the output directory.
    :param target_objects: Objects for which to save ground truth poses in BOP format. Default: Save all objects or
                           from specified dataset
    :param depths: List of depth images in m to save
    :param colors: List of color images to save
    :param color_file_format: File type to save color images. Available: "PNG", "JPEG"
    :param jpg_quality: If color_file_format is "JPEG", save with the given quality.
    :param dataset: Only save annotations for objects of the specified bop dataset. Saves all object poses if undefined.
    :param append_to_existing_output: If true, the new frames will be appended to the existing ones.
    :param depth_scale: Multiply the uint16 output depth image with this factor to get depth in mm. Used to trade-off
                        between depth accuracy and maximum depth value. Default corresponds to 65.54m maximum depth
                        and 1mm accuracy.
    :param save_world2cam: If true, camera to world transformations "cam_R_w2c", "cam_t_w2c" are saved
                           in scene_camera.json
    :param ignore_dist_thres: Distance between camera and object after which object is ignored. Mostly due to
                              failed physics.
    :param m2mm: Original bop annotations and models are in mm. If true, we convert the gt annotations to mm here. This
                 is needed if BopLoader option mm2m is used (deprecated).
    :param annotation_unit: The unit in which the annotations are saved. Available: 'm', 'dm', 'cm', 'mm'.
    :param frames_per_chunk: Number of frames saved in each chunk (called scene in BOP)
    :param calc_mask_info_coco: Whether to calculate gt masks, gt info and gt coco annotations.
    :param delta: Tolerance used for estimation of the visibility masks (in [m]).
    :param num_worker: The number of processes to use to calculate gt_masks and gt_info. If None is given, number of cores is used.
    """

    # Output paths.
    dataset_dir = os.path.join(output_dir, dataset)
    chunks_dir = os.path.join(dataset_dir, 'train_pbr')
    camera_path = os.path.join(dataset_dir, 'camera.json')

    # Create the output directory structure.
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
        os.makedirs(chunks_dir)
    elif not append_to_existing_output:
        raise FileExistsError(f"The output folder already exists: {dataset_dir}")

    # Select target objects or objects from the specified dataset or all objects
    if target_objects is not None:
        dataset_objects = target_objects
        for obj in dataset_objects:
            if obj.is_hidden():
                print(f"WARNING: The given object {obj.get_name()} is hidden. However, the bop writer will still add "
                      "coco annotations for it. If this is not desired, don't pass the object to the bop writer.")
    elif dataset:
        dataset_objects = []
        for obj in get_all_mesh_objects():
            if "bop_dataset_name" in obj.blender_obj and not obj.is_hidden():
                if obj.blender_obj["bop_dataset_name"] == dataset:
                    dataset_objects.append(obj)
    else:
        dataset_objects = []
        for obj in get_all_mesh_objects():
            if not obj.is_hidden():
                dataset_objects.append(obj)

    # Check if there is any object from the specified dataset.
    if not dataset_objects:
        raise RuntimeError(f"The scene does not contain any object from the specified dataset: {dataset}. "
                           f"Either remove the dataset parameter or assign custom property 'bop_dataset_name'"
                           f" to selected objects")

    if calc_mask_info_coco:
        # It might be that a chunk dir already exists where the writer appends frames.
        # If one (or multiple) more chunk dirs are created to save the rendered frames to,
        # mask/info/coco annotations need to be calculated for all of them
        chunk_dirs = sorted(glob.glob(os.path.join(chunks_dir, '*')))
        chunk_dirs = [d for d in chunk_dirs if os.path.isdir(d)]
        last_chunk_dir = sorted(chunk_dirs)[-1] if chunk_dirs else None

        starting_chunk_id = 0
        starting_frame_id = 0
        if last_chunk_dir:
            last_chunk_gt_fpath = os.path.join(last_chunk_dir, 'scene_gt.json')
            chunk_gt = _BopWriterUtility.load_json(last_chunk_gt_fpath, keys_to_int=True)

            # Current chunk and frame ID's.
            starting_chunk_id = int(os.path.basename(last_chunk_dir))
            starting_frame_id = int(sorted(chunk_gt.keys())[-1]) + 1

            if starting_frame_id % frames_per_chunk == 0:
                starting_chunk_id += 1
                starting_frame_id = 0

    # Save the data.
    _BopWriterUtility.write_camera(camera_path, depth_scale=depth_scale)
    assert annotation_unit in ['m', 'dm', 'cm', 'mm'], (f"Invalid annotation unit: `{annotation_unit}`. Supported "
                                                        f"are 'm', 'dm', 'cm', 'mm'")
    annotation_scale = {'m': 1., 'dm': 10., 'cm': 100., 'mm': 1000.}[annotation_unit]
    if m2mm is not None:
        warnings.warn("WARNING: `m2mm` is deprecated, please use `annotation_scale='mm'` instead!")
        annotation_scale = 1000.
    _BopWriterUtility.write_frames(chunks_dir, dataset_objects=dataset_objects, depths=depths, colors=colors,
                                   color_file_format=color_file_format, frames_per_chunk=frames_per_chunk,
                                   annotation_scale=annotation_scale, ignore_dist_thres=ignore_dist_thres,
                                   save_world2cam=save_world2cam, depth_scale=depth_scale, jpg_quality=jpg_quality)

    if calc_mask_info_coco:
        # Set up the bop toolkit
        SetupUtility.setup_pip(["git+https://github.com/thodan/bop_toolkit", "PyOpenGL==3.1.0"])

        # determine which objects to add to the vsipy renderer
        # for numpy>=1.20, np.float is deprecated: https://numpy.org/doc/stable/release/1.20.0-notes.html#deprecations
        np.float = float

        # Determine for which directories mask_info_coco has to be calculated
        chunk_dirs = sorted(glob.glob(os.path.join(chunks_dir, '*')))
        chunk_dirs = [d for d in chunk_dirs if os.path.isdir(d)]
        chunk_dir_ids = [d.split('/')[-1] for d in chunk_dirs]
        chunk_dirs = chunk_dirs[chunk_dir_ids.index(f"{starting_chunk_id:06d}"):]

        # convert all objects to trimesh objects
        trimesh_objects = {}
        for obj in dataset_objects:
            if obj.get_cp('category_id') in trimesh_objects:
                continue
            if isinstance(obj, Link):
                if not obj.visuals:
                    continue
                if len(obj.visuals) > 1:
                    warnings.warn('BOP Writer only supports saving annotations of one visual mesh per Link')
            trimesh_obj = obj.mesh_as_trimesh()
            # here we also add the scale factor of the objects. the position of the pyrender camera will change based
            # on the initial scale factor of the objects and the saved annotation format
            if not np.all(np.isclose(np.array(obj.blender_obj.scale), obj.blender_obj.scale[0])):
                print("WARNING: the scale is not the same across all dimensions, writing bop_toolkit annotations with "
                      "the bop writer will fail!")
            trimesh_objects[obj.get_cp('category_id')] = trimesh_obj

        # Create pool and init each worker
        width = bpy.context.scene.render.resolution_x
        height = bpy.context.scene.render.resolution_y
        pool = Pool(num_worker, initializer=_BopWriterUtility._pyrender_init, initargs=[width, height, trimesh_objects])

        _BopWriterUtility.calc_gt_masks(chunk_dirs=chunk_dirs, starting_frame_id=starting_frame_id,
                                        annotation_scale=annotation_scale, delta=delta, pool=pool)
         
        _BopWriterUtility.calc_gt_info(chunk_dirs=chunk_dirs, starting_frame_id=starting_frame_id,
                                       annotation_scale=annotation_scale, delta=delta, pool=pool)

        _BopWriterUtility.calc_gt_coco(chunk_dirs=chunk_dirs, dataset_objects=dataset_objects,
                                       starting_frame_id=starting_frame_id)
        
        pool.close()
        pool.join()



def bop_pose_to_pyrender_coordinate_system(cam_R_m2c: np.ndarray, cam_t_m2c: np.ndarray) -> np.ndarray:
    """ Converts an object pose in bop format to pyrender camera coordinate system
        (https://pyrender.readthedocs.io/en/latest/examples/cameras.html).

    :param cam_R_m2c: 3x3 Rotation matrix.
    :param cam_t_m2c: Translation vector.
    :return: Pose in pyrender coordinate system.
    """
    # create homogeneous transformation matrix
    bop_pose = np.eye(4)
    bop_pose[:3, :3] = cam_R_m2c
    bop_pose[:3, 3] = cam_t_m2c

    return change_target_coordinate_frame_of_transformation_matrix(bop_pose, ["X", "-Y", "-Z"])


class _BopWriterUtility:
    """ Saves the synthesized dataset in the BOP format. The dataset is split
        into chunks which are saved as individual "scenes". For more details
        about the BOP format, visit the BOP toolkit docs:
        https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md

    """

    @staticmethod
    def load_json(path, keys_to_int=False):
        """Loads content of a JSON file.
        From the BOP toolkit (https://github.com/thodan/bop_toolkit).

        :param path: Path to the JSON file.
        :param keys_to_int: Convert digit dict keys to integers. Default: False
        :return: Content of the loaded JSON file.
        """

        # Keys to integers.
        def convert_keys_to_int(x):
            return {int(k) if k.lstrip('-').isdigit() else k: v for k, v in x.items()}

        with open(path, 'r', encoding="utf-8") as f:
            if keys_to_int:
                content = json.load(f, object_hook=convert_keys_to_int)
            else:
                content = json.load(f)

        return content

    @staticmethod
    def save_json(path, content):
        """ Saves the content to a JSON file in a human-friendly format.
        From the BOP toolkit (https://github.com/thodan/bop_toolkit).

        :param path: Path to the output JSON file.
        :param content: Dictionary/list to save.
        """
        text = ""
        with open(path, 'w', encoding="utf-8") as file:
            if isinstance(content, dict):
                text += '{\n'
                content_sorted = sorted(content.items(), key=lambda x: x[0])
                for elem_id, (k, v) in enumerate(content_sorted):
                    text += f'  "{k}": {json.dumps(v, sort_keys=True)}'
                    if elem_id != len(content) - 1:
                        text += ','
                    text += '\n'
                text += '}'
                file.write(text)
            elif isinstance(content, list):
                text += '[\n'
                for elem_id, elem in enumerate(content):
                    text += f'  {json.dumps(elem, sort_keys=True)}'
                    if elem_id != len(content) - 1:
                        text += ','
                    text += '\n'
                text += ']'
                file.write(text)
            else:
                json.dump(content, file, sort_keys=True)

    @staticmethod
    def save_depth(path: str, im: np.ndarray):
        """Saves a depth image (16-bit) to a PNG file.
        From the BOP toolkit (https://github.com/thodan/bop_toolkit).

        :param path: Path to the output depth image file.
        :param im: ndarray with the depth image to save.
        """
        if not path.endswith(".png"):
            raise ValueError('Only PNG format is currently supported.')

        im[im > 65535] = 65535
        im_uint16 = np.round(im).astype(np.uint16)

        # PyPNG library can save 16-bit PNG and is faster than imageio.imwrite().
        w_depth = png.Writer(im.shape[1], im.shape[0], greyscale=True, bitdepth=16)
        with open(path, 'wb') as f:
            w_depth.write(f, np.reshape(im_uint16, (-1, im.shape[1])))

    @staticmethod
    def write_camera(camera_path: str, depth_scale: float = 1.0):
        """ Writes camera.json into dataset_dir.
        :param camera_path: Path to camera.json
        :param depth_scale: Multiply the uint16 output depth image with this factor to get depth in mm.
        """
        # Use second frame for reading intrinsics (due to backwards compatibility)
        bpy.context.scene.frame_set(1)
        cam_K = _WriterUtility.get_cam_attribute(bpy.context.scene.camera, 'cam_K')
        camera = {'cx': cam_K[0][2],
                  'cy': cam_K[1][2],
                  'depth_scale': depth_scale,
                  'fx': cam_K[0][0],
                  'fy': cam_K[1][1],
                  'height': bpy.context.scene.render.resolution_y,
                  'width': bpy.context.scene.render.resolution_x}

        _BopWriterUtility.save_json(camera_path, camera)

    @staticmethod
    def get_frame_gt(dataset_objects: List[bpy.types.Mesh], unit_scaling: float, ignore_dist_thres: float,
                     destination_frame: Optional[List[str]] = None):
        """ Returns GT pose annotations between active camera and objects.
        
        :param dataset_objects: Save annotations for these objects.
        :param unit_scaling: 1000. for outputting poses in mm
        :param ignore_dist_thres: Distance between camera and object after which object is ignored.
                                  Mostly due to failed physics.
        :param destination_frame: Transform poses from Blender internal coordinates to OpenCV coordinates
        :return: A list of GT camera-object pose annotations for scene_gt.json
        """
        if destination_frame is None:
            destination_frame = ["X", "-Y", "-Z"]

        H_c2w_opencv = Matrix(_WriterUtility.get_cam_attribute(bpy.context.scene.camera, 'cam2world_matrix',
                                                               local_frame_change=destination_frame))

        frame_gt = []
        for obj in dataset_objects:
            if isinstance(obj, Link):
                if not obj.visuals:
                    continue
                if len(obj.visuals) > 1:
                    warnings.warn('BOP Writer only supports saving poses of one visual mesh per Link')
                H_m2w = Matrix(obj.get_visual_local2world_mats()[0])
            else:
                H_m2w = Matrix(obj.get_local2world_mat())
                assert obj.has_cp("category_id"), f"{obj.get_name()} object has no custom property 'category_id'"

            cam_H_m2c = H_c2w_opencv.inverted() @ H_m2w
            cam_R_m2c = cam_H_m2c.to_quaternion().to_matrix()
            cam_t_m2c = cam_H_m2c.to_translation()

            # ignore examples that fell through the plane
            if not np.linalg.norm(list(cam_t_m2c)) > ignore_dist_thres:
                cam_t_m2c = list(cam_t_m2c * unit_scaling)
                frame_gt.append({
                    'cam_R_m2c': list(cam_R_m2c[0]) + list(cam_R_m2c[1]) + list(cam_R_m2c[2]),
                    'cam_t_m2c': cam_t_m2c,
                    'obj_id': obj.get_cp("category_id") if not isinstance(obj, Link) else obj.visuals[0].get_cp(
                        'category_id')
                })
            else:
                print('ignored obj, ', obj.get_cp("category_id"), 'because either ')
                print('(1) it is further away than parameter "ignore_dist_thres: ",', ignore_dist_thres)
                print('(e.g. because it fell through a plane during physics sim)')
                print('or')
                print('(2) the object pose has not been given in meters')

        return frame_gt

    @staticmethod
    def get_frame_camera(save_world2cam: bool, depth_scale: float = 1.0, unit_scaling: float = 1000.,
                         destination_frame: Optional[List[str]] = None):
        """ Returns camera parameters for the active camera.

        :param save_world2cam: If true, camera to world transformations "cam_R_w2c", "cam_t_w2c" are saved
                               in scene_camera.json
        :param depth_scale: Multiply the uint16 output depth image with this factor to get depth in mm.
        :param unit_scaling: 1000. for outputting poses in mm
        :param destination_frame: Transform poses from Blender internal coordinates to OpenCV coordinates
        :return: dict containing info for scene_camera.json
        """
        if destination_frame is None:
            destination_frame = ["X", "-Y", "-Z"]

        cam_K = _WriterUtility.get_cam_attribute(bpy.context.scene.camera, 'cam_K')

        frame_camera_dict = {
            'cam_K': cam_K[0] + cam_K[1] + cam_K[2],
            'depth_scale': depth_scale
        }

        if save_world2cam:
            H_c2w_opencv = Matrix(_WriterUtility.get_cam_attribute(bpy.context.scene.camera, 'cam2world_matrix',
                                                                   local_frame_change=destination_frame))

            H_w2c_opencv = H_c2w_opencv.inverted()
            R_w2c_opencv = H_w2c_opencv.to_quaternion().to_matrix()
            t_w2c_opencv = H_w2c_opencv.to_translation() * unit_scaling

            frame_camera_dict['cam_R_w2c'] = list(R_w2c_opencv[0]) + list(R_w2c_opencv[1]) + list(R_w2c_opencv[2])
            frame_camera_dict['cam_t_w2c'] = list(t_w2c_opencv)

        return frame_camera_dict

    @staticmethod
    def write_frames(chunks_dir: str, dataset_objects: list, depths: List[np.ndarray],
                     colors: List[np.ndarray], color_file_format: str = "PNG",
                     depth_scale: float = 1.0, frames_per_chunk: int = 1000, annotation_scale: float = 1000.,
                     ignore_dist_thres: float = 100., save_world2cam: bool = True, jpg_quality: int = 95):
        """Write each frame's ground truth into chunk directory in BOP format

        :param chunks_dir: Path to the output directory of the current chunk.
        :param dataset_objects: Save annotations for these objects.
        :param depths: List of depth images in m to save
        :param colors: List of color images to save
        :param color_file_format: File type to save color images. Available: "PNG", "JPEG"
        :param jpg_quality: If color_file_format is "JPEG", save with the given quality.
        :param depth_scale: Multiply the uint16 output depth image with this factor to get depth in mm. Used to
                            trade-off between depth accuracy and maximum depth value. Default corresponds to
                            65.54m maximum depth and 1mm accuracy.
        :param ignore_dist_thres: Distance between camera and object after which object is ignored.
                                  Mostly due to failed physics.
        :param annotation_scale: The scale factor applied to the calculated annotations (in [m]) to get them into the
                                 specified format (see `annotation_format` in `write_bop` for further details).
        :param frames_per_chunk: Number of frames saved in each chunk (called scene in BOP)
        """

        # Format of the depth images.
        depth_ext = '.png'

        rgb_tpath = os.path.join(chunks_dir, '{chunk_id:06d}', 'rgb', '{im_id:06d}' + '{im_type}')
        depth_tpath = os.path.join(chunks_dir, '{chunk_id:06d}', 'depth', '{im_id:06d}' + depth_ext)
        chunk_camera_tpath = os.path.join(chunks_dir, '{chunk_id:06d}', 'scene_camera.json')
        chunk_gt_tpath = os.path.join(chunks_dir, '{chunk_id:06d}', 'scene_gt.json')

        # Paths to the already existing chunk folders (such folders may exist
        # when appending to an existing dataset).
        chunk_dirs = sorted(glob.glob(os.path.join(chunks_dir, '*')))
        chunk_dirs = [d for d in chunk_dirs if os.path.isdir(d)]

        # Get ID's of the last already existing chunk and frame.
        curr_chunk_id = 0
        curr_frame_id = 0
        if len(chunk_dirs):
            last_chunk_dir = sorted(chunk_dirs)[-1]
            last_chunk_gt_fpath = os.path.join(last_chunk_dir, 'scene_gt.json')
            chunk_gt = _BopWriterUtility.load_json(last_chunk_gt_fpath, keys_to_int=True)

            # Last chunk and frame ID's.
            last_chunk_id = int(os.path.basename(last_chunk_dir))
            last_frame_id = int(sorted(chunk_gt.keys())[-1])

            # Current chunk and frame ID's.
            curr_chunk_id = last_chunk_id
            curr_frame_id = last_frame_id + 1
            if curr_frame_id % frames_per_chunk == 0:
                curr_chunk_id += 1
                curr_frame_id = 0

        # Initialize structures for the GT annotations and camera info.
        chunk_gt = {}
        chunk_camera = {}
        if curr_frame_id != 0:
            # Load GT and camera info of the chunk we are appending to.
            chunk_gt = _BopWriterUtility.load_json(
                chunk_gt_tpath.format(chunk_id=curr_chunk_id), keys_to_int=True)
            chunk_camera = _BopWriterUtility.load_json(
                chunk_camera_tpath.format(chunk_id=curr_chunk_id), keys_to_int=True)

        # Go through all frames.
        num_new_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start

        if len(depths) != len(colors) != num_new_frames:
            raise Exception("The amount of images stored in the depths/colors does not correspond to the amount"
                            "of images specified by frame_start to frame_end.")

        for frame_id in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            # Activate frame.
            bpy.context.scene.frame_set(frame_id)

            # Reset data structures and prepare folders for a new chunk.
            if curr_frame_id == 0:
                chunk_gt = {}
                chunk_camera = {}
                os.makedirs(os.path.dirname(
                    rgb_tpath.format(chunk_id=curr_chunk_id, im_id=0, im_type='PNG')))
                os.makedirs(os.path.dirname(
                    depth_tpath.format(chunk_id=curr_chunk_id, im_id=0)))

            # Get GT annotations and camera info for the current frame.
            chunk_gt[curr_frame_id] = _BopWriterUtility.get_frame_gt(dataset_objects, annotation_scale,
                                                                     ignore_dist_thres)
            chunk_camera[curr_frame_id] = _BopWriterUtility.get_frame_camera(save_world2cam, depth_scale,
                                                                             annotation_scale)

            color_rgb = colors[frame_id]
            color_bgr = color_rgb.copy()
            color_bgr[..., :3] = color_bgr[..., :3][..., ::-1]
            if color_file_format == 'PNG':
                rgb_fpath = rgb_tpath.format(chunk_id=curr_chunk_id, im_id=curr_frame_id, im_type='.png')
                cv2.imwrite(rgb_fpath, color_bgr)
            elif color_file_format == 'JPEG':
                rgb_fpath = rgb_tpath.format(chunk_id=curr_chunk_id, im_id=curr_frame_id, im_type='.jpg')
                cv2.imwrite(rgb_fpath, color_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])

            depth = depths[frame_id]

            # Scale the depth to retain a higher precision (the depth is saved
            # as a 16-bit PNG image with range 0-65535).
            depth_mm = 1000.0 * depth  # [m] -> [mm]
            depth_mm_scaled = depth_mm / float(depth_scale)

            # Save the scaled depth image.
            depth_fpath = depth_tpath.format(chunk_id=curr_chunk_id, im_id=curr_frame_id)
            _BopWriterUtility.save_depth(depth_fpath, depth_mm_scaled)

            # Save the chunk info if we are at the end of a chunk or at the last new frame.
            if ((curr_frame_id + 1) % frames_per_chunk == 0) or \
                    (frame_id == num_new_frames - 1):

                # Save GT annotations.
                _BopWriterUtility.save_json(chunk_gt_tpath.format(chunk_id=curr_chunk_id), chunk_gt)

                # Save camera info.
                _BopWriterUtility.save_json(chunk_camera_tpath.format(chunk_id=curr_chunk_id), chunk_camera)

                # Update ID's.
                curr_chunk_id += 1
                curr_frame_id = 0
            else:
                curr_frame_id += 1
        

    @staticmethod
    def _pyrender_init(ren_width: int, ren_height: int, trimesh_objects: Dict[int, trimesh.Trimesh]):
        """ Initializes a worker process for calc_gt_masks and calc_gt_info

        :param ren_width: The width of the images to render.
        :param ren_height: The height of the images to render.
        :param trimesh_objects: A dict containing trimesh meshes for each object in the scene
        """
        # pylint: disable=import-outside-toplevel
        # Import pyrender only inside the multiprocesses, otherwise this leads to an opengl error
        # https://github.com/mmatl/pyrender/issues/200#issuecomment-1123713055        
        import pyrender
        # pylint: enable=import-outside-toplevel

        global renderer, renderer_large, dataset_objects

        dataset_objects = {}
        # Create renderer for calc_gt_masks
        renderer = pyrender.OffscreenRenderer(viewport_width=ren_width, viewport_height=ren_height)
        # Create renderer for calc_gt_info
        renderer_large = pyrender.OffscreenRenderer(viewport_width=ren_width * 3, viewport_height=ren_height * 3)
        # Create pyrender meshes
        for key in trimesh_objects.keys():
            # we need to create a double-sided material to be able to render non-watertight meshes
            # the other parameters are defaults, see
            # https://github.com/mmatl/pyrender/blob/master/pyrender/mesh.py#L216-L223
            material = pyrender.MetallicRoughnessMaterial(alphaMode='BLEND', baseColorFactor=[0.3, 0.3, 0.3, 1.0],
                                                          metallicFactor=0.2, roughnessFactor=0.8, doubleSided=True)
            dataset_objects[key] = pyrender.Mesh.from_trimesh(mesh=trimesh_objects[key], material=material)


    @staticmethod
    def _calc_gt_masks_iteration(annotation_scale: float, K: np.ndarray, delta: float, dist_im: np.ndarray, chunk_dir: str, im_id: int, gt_data: Tuple[int, Dict[str, int]]):
        """ One iteration of calc_gt_masks(), executed inside a worker process.

        
        :param annotation_scale: The scale factor applied to the calculated annotations (in [m]) to get them into the
                                 specified format (see `annotation_format` in `write_bop` for further details).
        :param K: The camera instrinsics to use.
        :param delta: Tolerance used for estimation of the visibility masks.
        :param dist_im: The distance image of the frame.
        :param chunk_dir: The chunk dir where to store the resulting images.
        :param im_id: The id of the current image/frame.
        :param gt_data: Containing id of the object whose mask the worker should render
        """
        # pylint: disable=import-outside-toplevel
        # Import pyrender only inside the multiprocesses, otherwise this leads to an opengl error
        # https://github.com/mmatl/pyrender/issues/200#issuecomment-1123713055     
        import pyrender
        # This import is done inside to avoid having the requirement that BlenderProc depends on the bop_toolkit
        from bop_toolkit_lib import inout, misc, visibility
        # pylint: enable=import-outside-toplevel

        global renderer, dataset_objects

        gt_id, gt = gt_data

        # Init pyrender camera
        fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
        camera = pyrender.IntrinsicsCamera(fx=fx, fy=fy, cx=cx, cy=cy, znear=0.1, zfar=100000)
        
        # create a new scene
        scene = pyrender.Scene()

        # add camera and current object
        scene.add(camera)
        t = np.array(gt['cam_t_m2c'])
        # rescale translation depending on initial saving format
        t /= annotation_scale

        pose = bop_pose_to_pyrender_coordinate_system(cam_R_m2c=np.array(gt['cam_R_m2c']).reshape(3, 3),
                                                        cam_t_m2c=t)
        scene.add(dataset_objects[gt['obj_id']], pose=pose)

        # Render the depth image.
        _, depth_gt = renderer.render(scene=scene)

        # Convert depth image to distance image.
        dist_gt = misc.depth_im_to_dist_im_fast(depth_gt, K)

        # Mask of the full object silhouette.
        mask = dist_gt > 0

        # Mask of the visible part of the object silhouette.
        mask_visib = visibility.estimate_visib_mask_gt(
            dist_im, dist_gt, delta, visib_mode='bop19')

        # Save the calculated masks.
        mask_path = os.path.join(
            chunk_dir, 'mask', '{im_id:06d}_{gt_id:06d}.png').format(im_id=im_id, gt_id=gt_id)
        inout.save_im(mask_path, 255 * mask.astype(np.uint8))

        mask_visib_path = os.path.join(
            chunk_dir, 'mask_visib',
            '{im_id:06d}_{gt_id:06d}.png').format(im_id=im_id, gt_id=gt_id)
        inout.save_im(mask_visib_path, 255 * mask_visib.astype(np.uint8))


    @staticmethod
    def calc_gt_masks(pool: Pool, chunk_dirs: List[str], starting_frame_id: int = 0,
                      annotation_scale: float = 1000., delta: float = 0.015):
        """ Calculates the ground truth masks.
        From the BOP toolkit (https://github.com/thodan/bop_toolkit), with the difference of using pyrender for depth
        rendering.

        :param pool: The pool of worker processes to use for the calculations.
        :param chunk_dirs: List of directories to calculate the gt masks for.
        :param starting_frame_id: The first frame id the writer has written during this run.
        :param annotation_scale: The scale factor applied to the calculated annotations (in [m]) to get them into the
                                 specified format (see `annotation_format` in `write_bop` for further details).
        :param delta: Tolerance used for estimation of the visibility masks.
        """
        # This import is done inside to avoid having the requirement that BlenderProc depends on the bop_toolkit
        # pylint: disable=import-outside-toplevel
        from bop_toolkit_lib import inout, misc
        # pylint: enable=import-outside-toplevel

        for dir_counter, chunk_dir in enumerate(chunk_dirs):
            last_chunk_gt_fpath = os.path.join(chunk_dir, 'scene_gt.json')
            last_chunk_camera_fpath = os.path.join(chunk_dir, 'scene_camera.json')
            scene_gt = _BopWriterUtility.load_json(last_chunk_gt_fpath, keys_to_int=True)
            scene_camera = _BopWriterUtility.load_json(last_chunk_camera_fpath, keys_to_int=True)

            # Create folders for the output masks (if they do not exist yet).
            mask_dir_path = os.path.dirname(os.path.join(chunk_dir, 'mask', '000000_000000.png'))
            misc.ensure_dir(mask_dir_path)

            mask_visib_dir_path = os.path.dirname(os.path.join(chunk_dir, 'mask_visib', '000000_000000.png'))
            misc.ensure_dir(mask_visib_dir_path)

            im_ids = sorted(scene_gt.keys())

            # append to existing output
            if dir_counter == 0:
                im_ids = im_ids[starting_frame_id:]

            for im_counter, im_id in enumerate(im_ids):
                if im_counter % 100 == 0:
                    misc.log(f'Calculating GT masks - {chunk_dir}, {im_counter}')

                K = np.array(scene_camera[im_id]['cam_K']).reshape(3, 3)

                # Load depth image.
                depth_path = os.path.join(
                    chunk_dir, 'depth', '{im_id:06d}.png').format(im_id=im_id)
                depth_im = inout.load_depth(depth_path)
                depth_im *= scene_camera[im_id]['depth_scale']  # to [mm]
                depth_im /= 1000.  # to [m]
                dist_im = misc.depth_im_to_dist_im_fast(depth_im, K)

                pool.map(partial(_BopWriterUtility._calc_gt_masks_iteration, annotation_scale, K, delta, dist_im, chunk_dir, im_id), enumerate(scene_gt[im_id]))
          
            

    @staticmethod
    def _calc_gt_info_iteration(annotation_scale: float, ren_cy_offset: int, ren_cx_offset: int, im_height: int, im_width: int, K: np.ndarray, delta: float, depth: np.ndarray, gt: Dict[str, int]):
        """ One iteration of calc_gt_info(), executed inside a worker process.
        
        :param annotation_scale: The scale factor applied to the calculated annotations (in [m]) to get them into the
                                 specified format (see `annotation_format` in `write_bop` for further details).
        :param ren_cy_offset: The y offset for cropping the rendered image.
        :param ren_cx_offset: The x offset for cropping the rendered image.
        :param im_height: The image height for cropping the rendered image.
        :param im_width: The image width for cropping the rendered image.
        :param K: The camera instrinsics to use.
        :param delta: Tolerance used for estimation of the visibility masks.
        :param depth: The depth image of the frame.
        :param gt: Containing id of the object whose mask the worker should render
        """         
        # Import pyrender only inside the multiprocesses, otherwise this leads to an opengl error
        # https://github.com/mmatl/pyrender/issues/200#issuecomment-1123713055   
        # pylint: disable=import-outside-toplevel
        import pyrender
        from bop_toolkit_lib import misc, visibility
        # pylint: enable=import-outside-toplevel

        global renderer_large, dataset_objects, renderer

        # Delete renderer of the previous calc_gt_masks() function, otherwise
        # we cannot make use of the same pyrender Meshes
        if renderer._renderer is not None:
            renderer._renderer.delete()
            renderer._renderer = None

        # Init pyrender camera
        fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
        im_size = (depth.shape[1], depth.shape[0])
        camera = pyrender.IntrinsicsCamera(fx=fx, fy=fy, cx=cx+ren_cx_offset, cy=cy+ren_cy_offset, znear=0.1,
                                            zfar=100000)
        
        # create a new scene
        scene = pyrender.Scene()

        # add camera and current object
        scene.add(camera)
        t = np.array(gt['cam_t_m2c'])
        # rescale translation depending on initial saving format
        t /= annotation_scale
        pose = bop_pose_to_pyrender_coordinate_system(cam_R_m2c=np.array(gt['cam_R_m2c']).reshape(3, 3),
                                                        cam_t_m2c=t)
        scene.add(dataset_objects[gt['obj_id']], pose=pose)

        # render the depth image
        _, depth_gt_large = renderer_large.render(scene=scene)

        depth_gt = depth_gt_large[
                    ren_cy_offset:(ren_cy_offset + im_height),
                    ren_cx_offset:(ren_cx_offset + im_width)]

        # Convert depth images to distance images.
        dist_gt = misc.depth_im_to_dist_im_fast(depth_gt, K)
        dist_im = misc.depth_im_to_dist_im_fast(depth, K)

        # Estimation of the visibility mask.
        visib_gt = visibility.estimate_visib_mask_gt(
            dist_im, dist_gt, delta, visib_mode='bop19')

        # Mask of the object in the GT pose.
        obj_mask_gt_large = depth_gt_large > 0
        obj_mask_gt = dist_gt > 0

        # Number of pixels in the whole object silhouette
        # (even in the truncated part).
        px_count_all = np.sum(obj_mask_gt_large)

        # Number of pixels in the object silhouette with a valid depth measurement
        # (i.e. with a non-zero value in the depth image).
        px_count_valid = np.sum(dist_im[obj_mask_gt] > 0)

        # Number of pixels in the visible part of the object silhouette.
        px_count_visib = visib_gt.sum()

        # Visible surface fraction.
        if px_count_all > 0:
            visib_fract = px_count_visib / float(px_count_all)
        else:
            visib_fract = 0.0

        # Bounding box of the whole object silhouette
        # (including the truncated part).
        bbox = [-1, -1, -1, -1]
        if px_count_visib > 0:
            ys, xs = obj_mask_gt_large.nonzero()
            ys -= ren_cy_offset
            xs -= ren_cx_offset
            bbox = misc.calc_2d_bbox(xs, ys, im_size)

        # Bounding box of the visible surface part.
        bbox_visib = [-1, -1, -1, -1]
        if px_count_visib > 0:
            ys, xs = visib_gt.nonzero()
            bbox_visib = misc.calc_2d_bbox(xs, ys, im_size)

        # Store the calculated info.
        return {
            'px_count_all': int(px_count_all),
            'px_count_valid': int(px_count_valid),
            'px_count_visib': int(px_count_visib),
            'visib_fract': float(visib_fract),
            'bbox_obj': [int(e) for e in bbox],
            'bbox_visib': [int(e) for e in bbox_visib]
        }

    @staticmethod
    def calc_gt_info(pool, chunk_dirs: List[str], starting_frame_id: int = 0,
                     annotation_scale: float = 1000., delta: float = 0.015):
        """ Calculates the ground truth masks.
        From the BOP toolkit (https://github.com/thodan/bop_toolkit), with the difference of using pyrender for depth
        rendering.

        :param chunk_dirs: List of directories to calculate the gt info for.
        :param starting_frame_id: The first frame id the writer has written during this run.
        :param annotation_scale: The scale factor applied to the calculated annotations (in [m]) to get them into the
                                 specified format (see `annotation_format` in `write_bop` for further details).
        :param delta: Tolerance used for estimation of the visibility masks.
        """
        # This import is done inside to avoid having the requirement that BlenderProc depends on the bop_toolkit
        # pylint: disable=import-outside-toplevel
        from bop_toolkit_lib import inout, misc
        # pylint: enable=import-outside-toplevel

        im_width, im_height = bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y
        ren_cx_offset, ren_cy_offset = im_width, im_height

        for dir_counter, chunk_dir in enumerate(chunk_dirs):
            last_chunk_gt_fpath = os.path.join(chunk_dir, 'scene_gt.json')
            last_chunk_camera_fpath = os.path.join(chunk_dir, 'scene_camera.json')
            scene_gt = _BopWriterUtility.load_json(last_chunk_gt_fpath, keys_to_int=True)
            scene_camera = _BopWriterUtility.load_json(last_chunk_camera_fpath, keys_to_int=True)

            # load existing gt info
            if dir_counter == 0 and starting_frame_id > 0:
                misc.log(f"Loading gt info from existing chunk dir - {chunk_dir}")
                scene_gt_info = _BopWriterUtility.load_json(os.path.join(chunk_dir, 'scene_gt_info.json'),
                                                            keys_to_int=True)
            else:
                scene_gt_info = {}

            im_ids = sorted(scene_gt.keys())

            # append to existing output
            if dir_counter == 0:
                im_ids = im_ids[starting_frame_id:]

            for im_counter, im_id in enumerate(im_ids):
                if im_counter % 100 == 0:
                    misc.log(f'Calculating GT info - {chunk_dir}, {im_counter}')

                # Load depth image.
                depth_fpath = os.path.join(chunk_dir, 'depth', '{im_id:06d}.png').format(im_id=im_id)
                assert os.path.isfile(depth_fpath)
                depth = inout.load_depth(depth_fpath)
                depth *= scene_camera[im_id]['depth_scale']  # Convert to [mm].
                depth /= 1000.  # to [m]

                K = np.array(scene_camera[im_id]['cam_K']).reshape(3, 3)

                scene_gt_info[im_id] = pool.map(partial(_BopWriterUtility._calc_gt_info_iteration, annotation_scale, ren_cy_offset, ren_cx_offset, im_height, im_width, K, delta, depth), scene_gt[im_id])
                    

            # Save the info for the current scene.
            scene_gt_info_path = os.path.join(chunk_dir, 'scene_gt_info.json')
            misc.ensure_dir(os.path.dirname(scene_gt_info_path))
            inout.save_json(scene_gt_info_path, scene_gt_info)

    @staticmethod
    def calc_gt_coco(chunk_dirs: List[str], dataset_objects: List[MeshObject], starting_frame_id: int = 0):
        """ Calculates the COCO annotations.
        From the BOP toolkit (https://github.com/thodan/bop_toolkit).

        :param chunk_dirs: List of directories to calculate the gt coco annotations for.
        :param dataset_objects: List containing all objects to save the annotations for.
        :param starting_frame_id: The first frame id the writer has written during this run.
        """
        # This import is done inside to avoid having the requirement that BlenderProc depends on the bop_toolkit
        # pylint: disable=import-outside-toplevel
        from bop_toolkit_lib import inout, misc, pycoco_utils
        # pylint: enable=import-outside-toplevel

        for dir_counter, chunk_dir in enumerate(chunk_dirs):
            dataset_name = chunk_dir.split('/')[-3]

            CATEGORIES = [{'id': obj.get_cp('category_id'), 'name': str(obj.get_cp('category_id')), 'supercategory':
                          dataset_name} for obj in dataset_objects]

            # Remove all duplicate dicts from list.
            # Ref: https://stackoverflow.com/questions/9427163/remove-duplicate-dict-in-list-in-python
            CATEGORIES = list({frozenset(item.items()):item for item in CATEGORIES}.values())

            INFO = {
                "description": dataset_name + '_train',
                "url": "https://github.com/thodan/bop_toolkit",
                "version": "0.1.0",
                "year": datetime.date.today().year,
                "contributor": "",
                "date_created": datetime.datetime.utcnow().isoformat(' ')
            }

            # load existing coco annotations
            if dir_counter == 0 and starting_frame_id > 0:
                misc.log(f"Loading coco annotations from existing chunk dir - {chunk_dir}")
                coco_scene_output = _BopWriterUtility.load_json(os.path.join(chunk_dir, 'scene_gt_coco.json'))
                if coco_scene_output["annotations"]:
                    segmentation_id = coco_scene_output["annotations"][-1]['id'] + 1
                else:
                    segmentation_id = 1
            else:
                coco_scene_output = {
                    "info": INFO,
                    "licenses": [],
                    "categories": CATEGORIES,
                    "images": [],
                    "annotations": []
                }
                segmentation_id = 1

            # Load info about the GT poses (e.g. visibility) for the current scene.
            last_chunk_gt_fpath = os.path.join(chunk_dir, 'scene_gt.json')
            scene_gt = _BopWriterUtility.load_json(last_chunk_gt_fpath, keys_to_int=True)
            last_chunk_gt_info_fpath = os.path.join(chunk_dir, 'scene_gt_info.json')
            scene_gt_info = inout.load_json(last_chunk_gt_info_fpath, keys_to_int=True)
            # Output coco path
            coco_gt_path = os.path.join(chunk_dir, 'scene_gt_coco.json')
            misc.log(f'Calculating COCO annotations - {chunk_dir}')

            # Go through each view in scene_gt
            for scene_view, inst_list in scene_gt.items():
                im_id = int(scene_view)

                # skip already existing annotations
                if dir_counter == 0 and im_id < starting_frame_id:
                    continue

                img_path = os.path.join(chunk_dir, 'rgb', '{im_id:06d}.jpg').format(im_id=im_id)
                relative_img_path = os.path.relpath(img_path, os.path.dirname(coco_gt_path))
                im_size = (bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
                image_info = pycoco_utils.create_image_info(im_id, relative_img_path, im_size)
                coco_scene_output["images"].append(image_info)
                gt_info = scene_gt_info[scene_view]

                # Go through each instance in view
                for idx, inst in enumerate(inst_list):
                    category_info = inst['obj_id']
                    visibility = gt_info[idx]['visib_fract']
                    # Add ignore flag for objects smaller than 10% visible
                    ignore_gt = visibility < 0.1
                    mask_visib_p = os.path.join(
                        chunk_dir, 'mask_visib',
                        '{im_id:06d}_{gt_id:06d}.png').format(im_id=im_id, gt_id=idx)
                    mask_full_p = os.path.join(
                        chunk_dir, 'mask', '{im_id:06d}_{gt_id:06d}.png').format(im_id=im_id, gt_id=idx)

                    binary_inst_mask_visib = inout.load_depth(mask_visib_p).astype(bool)
                    if binary_inst_mask_visib.sum() < 1:
                        continue

                    # use `amodal` bbox type per default
                    binary_inst_mask_full = inout.load_depth(mask_full_p).astype(bool)
                    if binary_inst_mask_full.sum() < 1:
                        continue
                    bounding_box = pycoco_utils.bbox_from_binary_mask(binary_inst_mask_full)

                    annotation_info = pycoco_utils.create_annotation_info(
                        segmentation_id, im_id, category_info, binary_inst_mask_visib, bounding_box, tolerance=2,
                        ignore=ignore_gt)

                    if annotation_info is not None:
                        coco_scene_output["annotations"].append(annotation_info)

                    segmentation_id += 1

            with open(coco_gt_path, 'w', encoding='utf-8') as output_json_file:
                json.dump(coco_scene_output, output_json_file)
