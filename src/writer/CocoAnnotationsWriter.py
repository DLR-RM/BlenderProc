import bpy
import os
from src.utility.CocoUtility import CocoUtility
from src.main.Module import Module
import csv
import json


class CocoAnnotationsWriter(Module):
    """ Writes Coco Annotations in to a file.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "segmap_output_key", "The output key with which the segmentation images were registered. Should be the same as the output_key of the SegMapRenderer module."
       "segcolormap_output_key", "The output key with which the csv file for object name/class correspondences was registered. Should be the same as the colormap_output_key of the SegMapRenderer module."
    """

    def __init__(self, config):
        Module.__init__(self, config)

        self.segmap_output_key = self.config.get_string("segmap_output_key", "segmap")
        self.segcolormap_output_key = self.config.get_string("segcolormap_output_key", "segcolormap")

    def run(self):

        # Find path pattern of segmentation images
        segmentation_map_output = self._find_registered_output_by_key(self.segmap_output_key)
        if segmentation_map_output is None:
            raise Exception("There is no output registered with key " + self.segmap_output_key + ". Are you sure you ran the SegMapRenderer module before?")

        # collect all segmaps
        segmentation_map_paths = []
        # for each rendered frame
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
            segmentation_map_paths.append(segmentation_map_output["path"] % frame)

        # Find path of name class mapping csv file
        segcolormap_output = self._find_registered_output_by_key(self.segcolormap_output_key)
        if segcolormap_output is None:
            raise Exception("There is no output registered with key " + self.segcolormap_output_key + ". Are you sure you ran the SegMapRenderer module with 'map_by' set to 'instance' before?")

        # read colormappings, which include object name/class to integer mapping
        color_map = []
        with open(segcolormap_output["path"], 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for mapping in reader:
                color_map.append(mapping)

        coco_output = CocoUtility.generate_coco_annotations(segmentation_map_paths, color_map, "coco_annotations")
        fname = os.path.join(self._determine_output_dir(False), "coco_annotations.json")
        print("Writing coco annotations to " + fname)
        with open(fname, 'w') as fp:
            json.dump(coco_output, fp)
