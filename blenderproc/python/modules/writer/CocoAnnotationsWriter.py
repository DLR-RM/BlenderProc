from blenderproc.python.modules.main.GlobalStorage import GlobalStorage
from blenderproc.python.writer.CocoWriterUtility import write_coco_annotations
from blenderproc.python.modules.writer.WriterInterface import WriterInterface

import os

class CocoAnnotationsWriter(WriterInterface):
    """ Writes Coco Annotations in to a file.

    **Configuration**:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - rgb_output_key
          - The output key with which the rgb images were registered. Should be the same as the output_key of the
            RgbRenderer module. Default: colors.
          - string
        * - segmap_output_key
          - The output key with which the segmentation images were registered. Should be the same as the output_key
            of the SegMapRenderer module. Default: segmap.
          - string
        * - segcolormap_output_key
          - The output key with which the csv file for object name/class correspondences was registered. Should be
            the same as the colormap_output_key of the SegMapRenderer module. Default: segcolormap.
          - string
        * - supercategory
          - Name of the dataset/supercategory to filter for, e.g. a specific BOP dataset. Default: coco_annotations
          - string
        * - append_to_existing_output
          - If true and if there is already a coco_annotations.json file in the output directory, the new coco
            annotations will be appended to the existing file. Also the rgb images will be named such that there are
            no collisions. Default: False.
          - bool
        * - mask_encoding_format
          - Encoding format of the binary masks. Default: 'rle'. Available: 'rle', 'polygon'.
          - string
    """

    def __init__(self, config):
        WriterInterface.__init__(self, config)

        self.rgb_output_key = self.config.get_string("rgb_output_key", "colors")
        self._supercategory = self.config.get_string("supercategory", "coco_annotations")
        self.segmap_output_key = self.config.get_string("segmap_output_key", "segmap")
        self.segcolormap_output_key = self.config.get_string("segcolormap_output_key", "segcolormap")
        self.mask_encoding_format = self.config.get_string("mask_encoding_format", "rle")
        self._append_to_existing_output = self.config.get_bool("append_to_existing_output", False)

    def run(self):
        """ Writes coco annotations in the following steps:
        1. Locat the seg images
        2. Locat the rgb maps
        3. Locat the seg maps
        4. Read color mappings
        5. For each frame write the coco annotation
        """
        if self._avoid_output:
            print("Avoid output is on, no output produced!")
            return

        # Check if a label mapping is registered which could be used for naming the categories.
        if GlobalStorage.is_in_storage("label_mapping"):
            label_mapping = GlobalStorage.get("label_mapping")
        else:
            label_mapping = None

        write_coco_annotations(os.path.join(self._determine_output_dir(False), 'coco_data'),
                                mask_encoding_format=self.mask_encoding_format,
                                supercategory=self._supercategory,
                                append_to_existing_output=self._append_to_existing_output,
                                segmap_output_key=self.segmap_output_key,
                                segcolormap_output_key=self.segcolormap_output_key,
                                rgb_output_key=self.rgb_output_key,
                                label_mapping=label_mapping)