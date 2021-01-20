import json
import os
import math
import glob
import numpy as np
import png
import shutil

import bpy
from mathutils import Euler, Matrix, Vector

from src.utility.BlenderUtility import get_all_mesh_objects, load_image
from src.utility.CameraUtility import CameraUtility
from src.utility.Utility import Utility
from src.writer.WriterInterface import WriterInterface


def load_json(path, keys_to_int=False):
    """Loads content of a JSON file.
    From the BOP toolkit (https://github.com/thodan/bop_toolkit).

    :param path: Path to the JSON file.
    :return: Content of the loaded JSON file.
    """
    # Keys to integers.
    def convert_keys_to_int(x):
        return {int(k) if k.lstrip('-').isdigit() else k: v for k, v in x.items()}

    with open(path, 'r') as f:
        if keys_to_int:
            content = json.load(f, object_hook=lambda x: convert_keys_to_int(x))
        else:
            content = json.load(f)

    return content


def save_json(path, content):
    """ Saves the content to a JSON file in a human-friendly format.
    From the BOP toolkit (https://github.com/thodan/bop_toolkit).

    :param path: Path to the output JSON file.
    :param content: Dictionary/list to save.
    """
    with open(path, 'w') as f:

        if isinstance(content, dict):
            f.write('{\n')
            content_sorted = sorted(content.items(), key=lambda x: x[0])
            for elem_id, (k, v) in enumerate(content_sorted):
                f.write(
                    '  \"{}\": {}'.format(k, json.dumps(v, sort_keys=True)))
                if elem_id != len(content) - 1:
                    f.write(',')
                f.write('\n')
            f.write('}')

        elif isinstance(content, list):
            f.write('[\n')
            for elem_id, elem in enumerate(content):
                f.write('  {}'.format(json.dumps(elem, sort_keys=True)))
                if elem_id != len(content) - 1:
                    f.write(',')
                f.write('\n')
            f.write(']')

        else:
            json.dump(content, f, sort_keys=True)


def save_depth(path, im):
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


class BopWriter(WriterInterface):
    """ Saves the synthesized dataset in the BOP format. The dataset is split
        into chunks which are saved as individual "scenes". For more details
        about the BOP format, visit the BOP toolkit docs:
        https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md

    **Attributes per object**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - dataset
          - Only save annotations for objects of the specified bop dataset. Saves all object poses if not defined.
            Default: ''
          - string
        * - append_to_existing_output
          - If true, the new frames will be appended to the existing ones. Default: False
          - bool
        * - ignore_dist_thres
          - Distance between camera and object after which object is ignored. Mostly due to failed physics. Default: 5.
          - float
        * - m2mm
          - Original bop annotations and models are in mm. If true, we convert the gt annotations to mm here. This
            is needed if BopLoader option mm2m is used. Default: True
          - bool
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)

        # Parse configuration.
        self.dataset = self.config.get_string("dataset", "")

        self.append_to_existing_output = self.config.get_bool("append_to_existing_output", False)

        # Distance in meteres to object after which it is ignored. Mostly due to failed physics.
        self._ignore_dist_thres = self.config.get_float("ignore_dist_thres", 5.)

        # Number of frames saved in each chunk.
        self.frames_per_chunk = 1000

        # Multiply the output depth image with this factor to get depth in mm.
        self.depth_scale = 0.1

        # Output translation gt in mm
        self._scale = 1000. if self.config.get_bool("m2mm", True) else 1.

        # Format of the depth images.
        depth_ext = '.png'

        # Output paths.
        base_path = self._determine_output_dir(False)
        self.dataset_dir = os.path.join(base_path, 'bop_data', self.dataset)
        self.chunks_dir = os.path.join(self.dataset_dir, 'train_pbr')
        self.camera_path = os.path.join(self.dataset_dir, 'camera.json')
        self.rgb_tpath = os.path.join(
            self.chunks_dir, '{chunk_id:06d}', 'rgb', '{im_id:06d}' + '{im_type}')
        self.depth_tpath = os.path.join(
            self.chunks_dir, '{chunk_id:06d}', 'depth', '{im_id:06d}' + depth_ext)
        self.chunk_camera_tpath = os.path.join(
            self.chunks_dir, '{chunk_id:06d}', 'scene_camera.json')
        self.chunk_gt_tpath = os.path.join(
            self.chunks_dir, '{chunk_id:06d}', 'scene_gt.json')

        # Create the output directory structure.
        if not os.path.exists(self.dataset_dir):
            os.makedirs(self.dataset_dir)
            os.makedirs(self.chunks_dir)
        elif not self.append_to_existing_output:
            raise Exception("The output folder already exists: {}.".format(
                self.dataset_dir))

    def run(self):
        """ Stores frames and annotations for objects from the specified dataset.
        """
        
        all_mesh_objects = get_all_mesh_objects()
	
        # Select objects from the specified dataset.
        if self.dataset:
            self.dataset_objects = []
            for obj in all_mesh_objects:
                if "bop_dataset_name" in obj:
                    if obj["bop_dataset_name"] == self.dataset:
                        self.dataset_objects.append(obj)
        else:
            self.dataset_objects = all_mesh_objects

        # Check if there is any object from the specified dataset.
        if not self.dataset_objects:
            raise Exception("The scene does not contain any object from the "
                            "specified dataset: {}. Either remove the dataset parameter "
                            "or assign custom property 'bop_dataset_name' to selected objects".format(self.dataset))

        # Get the camera.
        cam_ob = bpy.context.scene.camera
        self.cam = cam_ob.data
        self.cam_pose = (self.cam, cam_ob)

        # Save the data.
        self._write_camera()
        self._write_frames()

    def _get_camera_attribute(self, cam_pose, attribute_name):
        """ Returns the value of the requested attribute for the given object.

        :param cam_pose: camera pose
        :param attribute_name: The attribute name.
        :return: The attribute value.
        """
        cam, cam_ob = cam_pose

        if attribute_name == "fov_x":
            return cam.angle_x
        elif attribute_name == "fov_y":
            return cam.angle_y
        elif attribute_name == "shift_x":
            return cam.shift_x
        elif attribute_name == "shift_y":
            return cam.shift_y
        elif attribute_name == "half_fov_x":
            return cam.angle_x * 0.5
        elif attribute_name == "half_fov_y":
            return cam.angle_y * 0.5

        return super()._get_attribute(cam_ob, attribute_name)

    def _get_object_attribute(self, object, attribute_name):
        """ Returns the value of the requested attribute for the given object.

        :param object: The mesh object.
        :param attribute_name: The attribute name.
        :return: The attribute value.
        """
        if attribute_name == "id":
            return object["category_id"]

        return super()._get_attribute(object, attribute_name)

    def _write_camera(self):
        """ Writes camera.json into dataset_dir.
        """

        width = bpy.context.scene.render.resolution_x
        height = bpy.context.scene.render.resolution_y

        cam_K = CameraUtility.get_intrinsics_as_K_matrix()
        camera = {'cx': cam_K[0][2],
                  'cy': cam_K[1][2],
                  'depth_scale': self.depth_scale,
                  'fx': cam_K[0][0],
                  'fy': cam_K[1][1],
                  'height': height,
                  'width': width}

        save_json(self.camera_path, camera)

        return

    def _get_frame_gt(self):
        """ Returns GT annotations for the active camera.

        :return: A list of GT annotations.
        """
        camera_rotation = self._get_camera_attribute(self.cam_pose, 'rotation_euler')
        camera_translation = self._get_camera_attribute(self.cam_pose, 'location')
        H_c2w = Matrix.Translation(Vector(camera_translation)) @ Euler(
            camera_rotation, 'XYZ').to_matrix().to_4x4()

        # Blender to opencv coordinates.
        H_c2w_opencv = Utility.transform_matrix_to_blender_coord_frame(H_c2w, ["X", "-Y", "-Z"])
        frame_gt = []
        for idx, obj in enumerate(self.dataset_objects):
            object_rotation = self._get_object_attribute(obj, 'rotation_euler')
            object_translation = self._get_object_attribute(obj, 'location')
            H_m2w = Matrix.Translation(Vector(object_translation)) @ Euler(
                object_rotation, 'XYZ').to_matrix().to_4x4()

            cam_H_m2c = (H_m2w.inverted() @ H_c2w_opencv).inverted()

            cam_R_m2c = cam_H_m2c.to_quaternion().to_matrix()
            cam_R_m2c = list(cam_R_m2c[0]) + list(cam_R_m2c[1]) + list(cam_R_m2c[2])
            cam_t_m2c = cam_H_m2c.to_translation()

            # ignore examples that fell through the plane
            if not np.linalg.norm(list(cam_t_m2c)) > self._ignore_dist_thres:
                cam_t_m2c = list(cam_t_m2c * self._scale)
                frame_gt.append({
                    'cam_R_m2c': cam_R_m2c,
                    'cam_t_m2c': cam_t_m2c,
                    'obj_id': self._get_object_attribute(obj, 'id')
                })
            else:
                print('ignored obj, ', self._get_object_attribute(obj, 'id'), 'because either ')
                print('(1) it is too far (e.g. fell through a plane during physics sim)')
                print('or')
                print('(2) the object pose has not been given in meters')
                
        return frame_gt

    def _get_cam_in_word_pose(self):
        """
        :return: Homogeneous of camera in word
        """
        camera_rotation = self._get_camera_attribute(self.cam_pose, 'rotation_euler')
        camera_translation = self._get_camera_attribute(self.cam_pose, 'location')
        H_c2w = Matrix.Translation(Vector(camera_translation)) @ Euler(
            camera_rotation, 'XYZ').to_matrix().to_4x4()

        # Blender to opencv coordinates.
        H_c2w_opencv = H_c2w @ Matrix.Rotation(math.radians(-180), 4, "X")
        H_c2w = []
        for i in range(4):
            H_c2w.append(list(H_c2w_opencv[i]))

        return H_c2w

    def _get_frame_camera(self):
        """ Returns camera parameters for the active camera.
        """
        return {
            'cam_K': np.hstack(CameraUtility.get_intrinsics_as_K_matrix()).tolist(),
            'depth_scale': self.depth_scale,
            'H_c2w': self._get_cam_in_word_pose()
        }

    def _write_frames(self):
        """ Writes images, GT annotations and camera info.
        """
        # Paths to the already existing chunk folders (such folders may exist
        # when appending to an existing dataset).
        chunk_dirs = sorted(glob.glob(os.path.join(self.chunks_dir, '*')))
        chunk_dirs = [d for d in chunk_dirs if os.path.isdir(d)]

        # Get ID's of the last already existing chunk and frame.
        curr_chunk_id = 0
        curr_frame_id = 0
        if len(chunk_dirs):
            last_chunk_dir = sorted(chunk_dirs)[-1]
            last_chunk_gt_fpath = os.path.join(last_chunk_dir, 'scene_gt.json')
            chunk_gt = load_json(last_chunk_gt_fpath, keys_to_int=True)

            # Last chunk and frame ID's.
            last_chunk_id = int(os.path.basename(last_chunk_dir))
            last_frame_id = int(sorted(chunk_gt.keys())[-1])

            # Current chunk and frame ID's.
            curr_chunk_id = last_chunk_id
            curr_frame_id = last_frame_id + 1
            if curr_frame_id % self.frames_per_chunk == 0:
                curr_chunk_id += 1
                curr_frame_id = 0

        # Initialize structures for the GT annotations and camera info.
        chunk_gt = {}
        chunk_camera = {}
        if curr_frame_id != 0:
            # Load GT and camera info of the chunk we are appending to.
            chunk_gt = load_json(
                self.chunk_gt_tpath.format(chunk_id=curr_chunk_id), keys_to_int=True)
            chunk_camera = load_json(
                self.chunk_camera_tpath.format(chunk_id=curr_chunk_id), keys_to_int=True)

        # Go through all frames.
        num_new_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start
        for frame_id in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            # Activate frame.
            bpy.context.scene.frame_set(frame_id)

            # Reset data structures and prepare folders for a new chunk.
            if curr_frame_id == 0:
                chunk_gt = {}
                chunk_camera = {}
                os.makedirs(os.path.dirname(
                    self.rgb_tpath.format(chunk_id=curr_chunk_id, im_id=0, im_type='PNG')))
                os.makedirs(os.path.dirname(
                    self.depth_tpath.format(chunk_id=curr_chunk_id, im_id=0)))

            # Get GT annotations and camera info for the current frame.
            chunk_gt[curr_frame_id] = self._get_frame_gt()
            chunk_camera[curr_frame_id] = self._get_frame_camera()

            # Copy the resulting RGB image.
            rgb_output = self._find_registered_output_by_key("colors")
            if rgb_output is None:
                raise Exception("RGB image has not been rendered.")
            image_type = '.png' if rgb_output['path'].endswith('png') else '.jpg'
            rgb_fpath = self.rgb_tpath.format(chunk_id=curr_chunk_id, im_id=curr_frame_id, im_type=image_type)
            shutil.copyfile(rgb_output['path'] % frame_id, rgb_fpath)

            # Load the resulting dist image.
            dist_output = self._find_registered_output_by_key("distance")
            if dist_output is None:
                raise Exception("Distance image has not been rendered.")
            depth, _, _ = self._load_and_postprocess(dist_output['path'] % frame_id, "distance")

            # Scale the depth to retain a higher precision (the depth is saved
            # as a 16-bit PNG image with range 0-65535).
            depth_mm = 1000.0 * depth  # [m] -> [mm]
            depth_mm_scaled = depth_mm / float(self.depth_scale)

            # Save the scaled depth image.
            depth_fpath = self.depth_tpath.format(chunk_id=curr_chunk_id, im_id=curr_frame_id)
            save_depth(depth_fpath, depth_mm_scaled)

            # Save the chunk info if we are at the end of a chunk or at the last new frame.
            if ((curr_frame_id + 1) % self.frames_per_chunk == 0) or\
                  (frame_id == num_new_frames - 1):

                # Save GT annotations.
                save_json(self.chunk_gt_tpath.format(chunk_id=curr_chunk_id), chunk_gt)

                # Save camera info.
                save_json(self.chunk_camera_tpath.format(chunk_id=curr_chunk_id), chunk_camera)

                # Update ID's.
                curr_chunk_id += 1
                curr_frame_id = 0
            else:
                curr_frame_id += 1

        return
