import bpy
import os
from src.utility.CocoUtility import CocoUtility
from src.main.Module import Module
import csv
import json


class CocoAnnotationsWriter(Module):
    """ Writes Coco Annotations in to a file.
    """

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        # get the segmap file for this scene

        annotated_images = []
        # collect all segmaps
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):  # for each rendered frame
            fname = os.path.join(self._determine_output_dir(), "segmap_" + "%04d" % frame)
            annotated_images.append(fname + '.npy')

        color_map = []
        # read colormappings, which include object name/class to integer mapping
        with open(os.path.join(self._determine_output_dir(), "class_inst_col_map.csv"), 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for mapping in reader:
                color_map.append(mapping)

        coco_output = CocoUtility.generate_coco_annotations(annotated_images, color_map, bpy.context.scene.objects, "coco_annotations")
        fname = os.path.join(self._determine_output_dir(False), "coco_annotations.json")
        with open(fname, 'w') as fp:
            json.dump(coco_output, fp)
