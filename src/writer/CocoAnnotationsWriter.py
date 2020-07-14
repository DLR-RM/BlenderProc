import csv
import json
import os
import shutil

import bpy

from src.writer.WriterInterface import WriterInterface
from src.utility.CocoUtility import CocoUtility
from src.utility.BlenderUtility import get_all_mesh_objects

class CocoAnnotationsWriter(WriterInterface):
    """ Writes Coco Annotations in to a file.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"
       
       "avoid_rendering", "If true, no output is produced. Type: bool. Default: False"
       "rgb_output_key", "The output key with which the rgb images were registered. Should be the same as the "
                         "output_key of the RgbRenderer module. Type: string.Default: colors."
       "segmap_output_key", "The output key with which the segmentation images were registered. Should be the same as "
                            "the output_key of the SegMapRenderer module. Type: string. Default: segmap."
       "segcolormap_output_key", "The output key with which the csv file for object name/class correspondences was "
                                 "registered. Should be the same as the colormap_output_key of the SegMapRenderer "
                                 "module. Type: string. Default: segcolormap."
       "supercategory", "Name of the dataset/supercategory to filter for, e.g. a specific BOP dataset."
                        "Type: str. Default: coco_annotations"
       "append_to_existing_output", "If true and if there is already a coco_annotations.json file in the output "
                                    "directory, the new coco annotations will be appended to the existing file. Also "
                                    "the rgb images will be named such that there are no collisions. Type: bool. "
                                    "Default: False."
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)

        self._avoid_rendering = config.get_bool("avoid_rendering", False)
        self.rgb_output_key = self.config.get_string("rgb_output_key", "colors")
        self._supercategory = self.config.get_string("supercategory", "coco_annotations")
        self.segmap_output_key = self.config.get_string("segmap_output_key", "segmap")
        self.segcolormap_output_key = self.config.get_string("segcolormap_output_key", "segcolormap")
        self._coco_data_dir = os.path.join(self._determine_output_dir(False), 'coco_data')
        if not os.path.exists(self._coco_data_dir):
            os.makedirs(self._coco_data_dir)

    def run(self):
        """ Writes coco annotations in the following steps:
        1. Locat the seg images
        2. Locat the rgb maps
        3. Locat the seg maps
        4. Read color mappings
        5. For each frame write the coco annotation
        """
        if self._avoid_rendering:
            print("Avoid rendering is on, no output produced!")
            return

        # Find path pattern of segmentation images
        segmentation_map_output = self._find_registered_output_by_key(self.segmap_output_key)
        if segmentation_map_output is None:
            raise Exception("There is no output registered with key " + self.segmap_output_key + ". Are you sure you ran the SegMapRenderer module before?")
        
        # Find path pattern of rgb images
        rgb_output = self._find_registered_output_by_key(self.rgb_output_key)
        if rgb_output is None:
            raise Exception("There is no output registered with key " + self.rgb_output_key + ". Are you sure you ran the RgbRenderer module before?")
    
        # collect all segmaps
        segmentation_map_paths = []

        # Find path of name class mapping csv file
        segcolormap_output = self._find_registered_output_by_key(self.segcolormap_output_key)
        if segcolormap_output is None:
            raise Exception("There is no output registered with key " + self.segcolormap_output_key + ". Are you sure you ran the SegMapRenderer module with 'map_by' set to 'instance' before?")

        # read colormappings, which include object name/class to integer mapping
        inst_attribute_maps = []
        with open(segcolormap_output["path"], 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for mapping in reader:
                inst_attribute_maps.append(mapping)

        coco_annotations_path = os.path.join(self._coco_data_dir, "coco_annotations.json")
        # Calculate image numbering offset, if append_to_existing_output is activated and coco data exists
        if self.config.get_bool("append_to_existing_output", False) and os.path.exists(coco_annotations_path):
            with open(coco_annotations_path, 'r') as fp:
                existing_coco_annotations = json.load(fp)
            image_offset = max([image["id"] for image in existing_coco_annotations["images"]]) + 1
        else:
            image_offset = 0
            existing_coco_annotations = None

        # collect all RGB paths
        new_coco_image_paths = []
        # for each rendered frame
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            segmentation_map_paths.append(segmentation_map_output["path"] % frame)

            source_path = rgb_output["path"] % frame
            target_path = os.path.join(self._coco_data_dir, os.path.basename(rgb_output["path"] % (frame + image_offset)))

            shutil.copyfile(source_path, target_path)
            new_coco_image_paths.append(os.path.basename(target_path))

        coco_output = CocoUtility.generate_coco_annotations(segmentation_map_paths, new_coco_image_paths, inst_attribute_maps, self._supercategory, existing_coco_annotations)

        print("Writing coco annotations to " + coco_annotations_path)
        with open(coco_annotations_path, 'w') as fp:
            json.dump(coco_output, fp)
