import json
import os
import math
import glob
import numpy as np
import png
import shutil

import bpy
from mathutils import Euler, Matrix, Vector

from src.utility.BlenderUtility import get_all_mesh_objects
from src.utility.BlenderUtility import load_image
from src.writer.StateWriter import StateWriter


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
    if path.split('.')[-1].lower() != 'png':
        raise ValueError('Only PNG format is currently supported.')

    im[im > 65535] = 65535
    im_uint16 = np.round(im).astype(np.uint16)

    # PyPNG library can save 16-bit PNG and is faster than imageio.imwrite().
    w_depth = png.Writer(im.shape[1], im.shape[0], greyscale=True, bitdepth=16)
    with open(path, 'wb') as f:
        w_depth.write(f, np.reshape(im_uint16, (-1, im.shape[1])))


class BopWriter(StateWriter):
    """ Saves the synthesized dataset in the BOP format. The dataset is split
        into chunks which are saved as individual "scenes". For more details
        about the BOP format, visit the BOP toolkit docs:
        https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md

    **Attributes per object**:

    .. csv-table::
       :header: "Keyword", "Description"

       "dataset", "Annotations for objects of this dataset will be saved. Type: string."
       "append_to_existing_output", "If true, the new frames will be appended to the existing ones. "
                                    "Type: bool. Default: False"
    """

    def __init__(self, config):
        StateWriter.__init__(self, config)

        # Parse configuration.
        self.dataset = self.config.get_string("dataset", "")
        if self.dataset == "":
            raise Exception("Dataset not specified.")
        self.append_to_existing_output =\
            self.config.get_bool("append_to_existing_output", False)

        # Number of frames saved in each "scene directory".
        self.frames_per_scene_dir = 1000

        # Format of the RGB and depth images.
        rgb_ext = '.png'
        depth_ext = '.png'

        # Multiply the output depth image with this factor to get depth in mm.
        self.depth_scale = 0.1

        # Output paths.
        base_path = self._determine_output_dir(False)
        self.dataset_dir = os.path.join(base_path, 'bop_data', self.dataset)
        self.scenes_dir = os.path.join(self.dataset_dir, 'train_synt')
        self.camera_path = os.path.join(self.dataset_dir, 'camera.json')
        self.rgb_tpath = os.path.join(
            self.scenes_dir, '{scene_id:06d}', 'rgb', '{im_id:06d}' + rgb_ext)
        self.depth_tpath = os.path.join(
            self.scenes_dir, '{scene_id:06d}', 'depth', '{im_id:06d}' + depth_ext)
        self.scene_camera_tpath = os.path.join(
            self.scenes_dir, '{scene_id:06d}', 'scene_camera.json')
        self.scene_gt_tpath = os.path.join(
            self.scenes_dir, '{scene_id:06d}', 'scene_gt.json')

        # Create the output directory structure.
        if not os.path.exists(self.dataset_dir):
            os.makedirs(self.dataset_dir)
            os.makedirs(self.scenes_dir)
        elif not self.append_to_existing_output:
            raise Exception("The output folder already exists: {}.".format(
                self.dataset_dir))

    def run(self):
        """ Stores frames and annotations for objects from the specified dataset.
        """
        # Select objects from the specified dataset.
        all_mesh_objects = get_all_mesh_objects()
        self.dataset_objects = []
        for obj in all_mesh_objects:
            if "bop_dataset_name" in obj:
                if obj["bop_dataset_name"] == self.dataset:
                    self.dataset_objects.append(obj)

        # Paths to the already existing scene folders (such folders may exist
        # when appending to an existing dataset).
        scene_dirs = sorted(glob.glob(os.path.join(self.scenes_dir, '*')))
        scene_dirs = [d for d in scene_dirs if os.path.isdir(d)]

        # Get the ID of the last already existing frame.
        self.frame_id_offset = 0
        if len(scene_dirs):
            last_scene_gt_fpath = os.path.join(sorted(scene_dirs)[-1], 'scene_gt.json')
            scene_gt = load_json(last_scene_gt_fpath, keys_to_int=True)
            self.frame_id_offset = int(sorted(scene_gt.keys())[-1]) + 1

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
        elif attribute_name == 'loaded_intrinsics':
            return cam['loaded_intrinsics']

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

    def get_camK_from_blender_attributes(self, cam_pose):
        """ Constructs the camera matrix K.

        :param cam_pose: Camera info.
        :return: 3x3 camera matrix K.
        """
        shift_x = self._get_camera_attribute(cam_pose, 'shift_x')
        shift_y = self._get_camera_attribute(cam_pose, 'shift_y')
        syn_cam_K = self._get_camera_attribute(cam_pose, 'loaded_intrinsics')
        width = bpy.context.scene.render.resolution_x
        height = bpy.context.scene.render.resolution_y

        cam_K = [0.] * 9
        cam_K[-1] = 1

        max_resolution = max(width, height)
        
        cam_K[0] = syn_cam_K[0]
        cam_K[4] = syn_cam_K[4]
 
        cam_K[2] = width/2. - shift_x * max_resolution
        cam_K[5] = height/2. + shift_y * max_resolution

        return cam_K

    def _write_camera(self):
        """ Writes camera.json into dataset_dir.
        """
        if 'loaded_resolution' in self.cam:
            width, height = self.cam['loaded_resolution']
        else:
            width = bpy.context.scene.render.resolution_x
            height = bpy.context.scene.render.resolution_y

        cam_K = self.get_camK_from_blender_attributes(self.cam_pose)
        camera = {'cx': cam_K[2],
                  'cy': cam_K[5],
                  'depth_scale': self.depth_scale,
                  'fx': cam_K[0],
                  'fy': cam_K[4],
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
        H_c2w_opencv = H_c2w @ Matrix.Rotation(math.radians(-180), 4, "X")

        frame_gt = []
        for idx, obj in enumerate(self.dataset_objects):
            object_rotation = self._get_object_attribute(obj, 'rotation_euler')
            object_translation = self._get_object_attribute(obj, 'location')
            H_m2w = Matrix.Translation(Vector(object_translation)) @ Euler(
                object_rotation, 'XYZ').to_matrix().to_4x4()

            cam_H_m2c = (H_m2w.inverted() @ H_c2w_opencv).inverted()

            cam_R_m2c = cam_H_m2c.to_quaternion().to_matrix()
            cam_R_m2c = list(cam_R_m2c[0]) + list(cam_R_m2c[1]) + list(cam_R_m2c[2])
            cam_t_m2c = list(cam_H_m2c.to_translation() * 1000.)

            frame_gt.append({
                'cam_R_m2c': cam_R_m2c,
                'cam_t_m2c': cam_t_m2c,
                'obj_id': self._get_object_attribute(obj, 'id')
            })

        return frame_gt

    def _get_frame_camera(self):
        """ Returns camera parameters for the active camera.
        """
        return {
            'cam_K': list(self.get_camK_from_blender_attributes(self.cam_pose)),
            'depth_scale': self.depth_scale
        }

    def _write_frames(self):
        """ Writes images, scene GT and scene camera info.
        """
        # Initialize structures for the GT annotations and camera info.
        if self.frame_id_offset % self.frames_per_scene_dir == 0:
            scene_gt = {}
            scene_camera = {}
        else:
            # Load GT and camera info of the scene we are appending to.
            scene_id = int(self.frame_id_offset / self.frames_per_scene_dir)
            scene_gt = load_json(self.scene_gt_tpath.format(scene_id=scene_id), keys_to_int=True)
            scene_camera = load_json(self.scene_camera_tpath.format(scene_id=scene_id), keys_to_int=True)

        # Go through all frames.
        num_new_frames = bpy.context.scene.frame_end - bpy.context.scene.frame_start
        for frame_id in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            # Activate frame.
            bpy.context.scene.frame_set(frame_id)

            # Frame and scene ID's.
            current_frame_id = frame_id + self.frame_id_offset
            scene_id = int(current_frame_id / self.frames_per_scene_dir)

            # Prepare folders for a new scene.
            if current_frame_id % self.frames_per_scene_dir == 0:
                os.makedirs(os.path.dirname(self.rgb_tpath.format(scene_id=scene_id, im_id=0)))
                os.makedirs(os.path.dirname(self.depth_tpath.format(scene_id=scene_id, im_id=0)))

            # Get GT annotations and camera info for the current frame.
            scene_gt[current_frame_id] = self._get_frame_gt()
            scene_camera[current_frame_id] = self._get_frame_camera()

            # Copy the resulting RGB image.
            rgb_output = self._find_registered_output_by_key("colors")
            rgb_fpath = self.rgb_tpath.format(scene_id=scene_id, im_id=current_frame_id)
            shutil.copyfile(rgb_output['path'] % frame_id, rgb_fpath)

            # Load the resulting depth image.
            depth_output = self._find_registered_output_by_key("depth")
            depth = load_image(depth_output['path'] % frame_id, num_channels=1)
            depth = depth.squeeze(axis=2)

            # Scale the depth to retain a higher precision (the depth is saved
            # as a 16-bit PNG image with range 0-65535).
            depth_mm = 1000.0 * depth  # [m] -> [mm]
            depth_mm_scaled = depth_mm / float(self.depth_scale)

            # Save the scaled depth image.
            depth_fpath = self.depth_tpath.format(scene_id=scene_id, im_id=current_frame_id)
            save_depth(depth_fpath, depth_mm_scaled)

            # Save the scene info if we are at the end of a scene/chunk or at
            # the last new frame.
            if ((current_frame_id + 1) % self.frames_per_scene_dir == 0) or\
                  (frame_id == num_new_frames - 1):

                # Save scene GT annotations.
                save_json(self.scene_gt_tpath.format(scene_id=scene_id), scene_gt)

                # Save scene camera info.
                save_json(self.scene_camera_tpath.format(scene_id=scene_id), scene_camera)

                # Reset structures for GT and camera info.
                scene_gt = {}
                scene_camera = {}

        return
