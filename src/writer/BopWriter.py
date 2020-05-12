import json
import os

import bpy
from mathutils import Euler

from src.utility.BlenderUtility import get_all_mesh_objects
from src.writer.StateWriter import StateWriter


class BopWriter(StateWriter):
    """ Writes objects and camera details for each frame according to the bop datasets format.
        For more details about the bop datasets visit the bop toolkit docs
        https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md

    **Attributes per object**:

    .. csv-table::
       :header: "Keyword", "Description"

       "append_to_existing_output", "If true and if there is already a scene_gt.json and scene_camera.json files in "
                                    "the output directory, the new frames will be appended to the existing files. "
                                    "Type: bool. Default: False"
    """

    def __init__(self, config):
        StateWriter.__init__(self, config)


    def initialize_bop_groups(self):
        # Get and group all objects belonging to different bop datasets
        all_mesh_objects = get_all_mesh_objects()
        bop_datasets = {}
        for obj in all_mesh_objects:
            if "bop_dataset_name" in obj:
                if obj["bop_dataset_name"] in bop_datasets:
                    bop_datasets[obj["bop_dataset_name"]].append(obj)
                else:
                    bop_datasets[obj["bop_dataset_name"]] = [obj]
        self.bop_datasets = bop_datasets

        # For each group, make a seperate output directory
        base_path = self._determine_output_dir(False)
        self._bop_data_dir = os.path.join(base_path, 'bop_data')
        # Create base directory if not exists
        if not os.path.exists(self._bop_data_dir):
            os.makedirs(self._bop_data_dir)
        # Create subdirectorys if don't exist
        self._bop_data_sub_dirs = {}
        for group in self.bop_datasets:
            self._bop_data_sub_dirs[group] = os.path.join(base_path, 'bop_data', group)
            if not os.path.exists(self._bop_data_sub_dirs[group]):
                os.makedirs(self._bop_data_sub_dirs[group])

        # For each subdirectory create internal file paths
        self._scene_gt_path = {}
        self._scene_camera_path = {}
        self._camera_path = {}
        for group in self.bop_datasets:
            self._scene_gt_path[group] = os.path.join(self._bop_data_sub_dirs[group], 'scene_gt.json') 
            self._scene_camera_path[group] = os.path.join(self._bop_data_sub_dirs[group], 'scene_camera.json') 
            self._camera_path[group] = os.path.join(self._bop_data_sub_dirs[group], 'camera.json')


    def run(self):
        """ Collects the camera and camera object then for each file to be written excutes its function"""
        # Initialize and group bop dataset objects
        self.initialize_bop_groups()

        # Collect camera and camera object
        cam_ob = bpy.context.scene.camera
        self.cam = cam_ob.data
        self.cam_pose = (self.cam, cam_ob)

        # for each bop dataset group
        for group in self.bop_datasets:       
            self._write_scene_gt(group)
            self._write_scene_camera(group)
            self._write_camera(group)

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

    def _write_scene_gt(self, bop_group): 
        """ Creates and writes scene_gt.json in output_dir.

        :return
        """
        scene_gt = {} 
        # Calculate image numbering offset, if append_to_existing_output is activated and scene ground truth exists
        if self.config.get_bool("append_to_existing_output", False) and os.path.exists(self._scene_gt_path[bop_group]):
            with open(self._scene_gt_path[bop_group], 'r') as fp:
                scene_gt = json.load(fp)
            frame_offset = int(sorted(scene_gt.keys())[-1])
        else:
            frame_offset = 0

        # Go Through all frames
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            bpy.context.scene.frame_set(frame)
            # We add one to match the numbering system of bop toolkit
            current_frame = frame + 1 + frame_offset
            scene_gt[current_frame] = []
            for idx, obj in enumerate(self.bop_datasets[bop_group]):
                
                # Convert the rotation_euler matrix into a list to match scene_gt fromat
                rotation_vector = self._get_object_attribute(obj, 'rotation_euler')
                rot_matrix_as_list = []
                for v in Euler(rotation_vector).to_matrix()[:]:
                    rot_matrix_as_list += list(v)
                
                scene_gt[current_frame].append({'cam_R_m2c': rot_matrix_as_list,
                                        'cam_t_m2c': list(1000*self._get_object_attribute(obj, 'location')),
                                        'obj_id': self._get_object_attribute(obj, 'id')})
            with open(self._scene_gt_path[bop_group], 'w') as scene_gt_file:
                json.dump(scene_gt, scene_gt_file)
        
        return

    def _write_scene_camera(self, bop_group):
        """ Creates and writes scene_camera.json in output_dir.

        :return
        """ 
        scene_camera = {} 
        # Calculate image numbering offset, if append_to_existing_output is activated and scene ground truth exists
        if self.config.get_bool("append_to_existing_output", False) and os.path.exists(self._scene_camera_path[bop_group]):
            with open(self._scene_camera_path[bop_group], 'r') as fp:
                scene_camera = json.load(fp)
            frame_offset = int(sorted(scene_camera.keys())[-1])
        else:
            frame_offset = 0 

        # Go Through all frames
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            bpy.context.scene.frame_set(frame)
            # We add one to match the numbering system of bop toolkit
            current_frame = frame + 1 + frame_offset
            scene_camera[current_frame] = {'cam_K': list(self._get_camera_attribute(self.cam_pose, 'loaded_intrinsics')),
                                   'depth_scale': 0.001}
            with open(self._scene_camera_path[bop_group], 'w') as scene_camera_file:
                json.dump(scene_camera, scene_camera_file)

        return

    def _write_camera(self, bop_group):
        """ Creates and writes camera.json in output_dir.

        :return
        """       
        if 'loaded_resolution' in self.cam:
            width, height = self.cam['loaded_resolution']
        else:
            width = bpy.context.scene.render.resolution_x
            height = bpy.context.scene.render.resolution_y

        cam_K = self._get_camera_attribute(self.cam_pose, 'loaded_intrinsics')
        camera = {'cx': cam_K[2],
                  'cy': cam_K[5],
                  'depth_scale': 0.001,
                  'fx': cam_K[0],
                  'fy': cam_K[4],
                  'height': height,
                  'width': width}

        with open(self._camera_path[bop_group], 'w') as camera_file:
            json.dump(camera, camera_file)

        return
