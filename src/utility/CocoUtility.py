import datetime
import numpy as np
from src.utility.Coco.pycococreatortools import PycocoCreatorTools

class CocoUtility:

    @staticmethod
    def generate_coco_annotations(annotated_images,colormap,objects, dataset_name):
        """Generates coco annotations for images
        Args:
            annotated_images: list of annotated images, where each pixel is its annotation
            colormap: mapping for color, class and object
            objects: list of all bpy mesh objects
            dataset_name: name of the dataset, a feature required by coco annotation format
        Returns:
            coco_output: dict containing coco annotations
        """
        CATEGORIES = [{'id': idx, 'name':str(obj.name), 'supercategory': dataset_name} for idx, obj in enumerate(objects) if obj.type == 'MESH']
        LICENSES = [
            {
                "id": 1,
                "name": "Attribution-NonCommercial-ShareAlike License",
                "url": "http://creativecommons.org/licenses/by-nc-sa/2.0/"
            }
        ]
        INFO = {
            "description": dataset_name,
            "url": "https://github.com/waspinator/pycococreator",
            "version": "0.1.0",
            "year": 2018,
            "contributor": "waspinator",
            "date_created": datetime.datetime.utcnow().isoformat(' ')
        }

        coco_output = {
            "info": INFO,
            "licenses": LICENSES,
            "categories": CATEGORIES,
            "images": [],
            "annotations": []
        }
        image_id = 0
        segmentation_id = 0
        for imfile in annotated_images:
            annotation = np.load(imfile)
            image_info = PycocoCreatorTools.create_image_info(image_id, imfile, annotation.shape)
            coco_output["images"].append(image_info)
            unique_objects = np.unique(annotation)
            unique_objects = np.delete(unique_objects,np.where( unique_objects == -1 ))
            for obj in unique_objects:
                binary_inst_mask = np.array([[1 if c == obj else 0 for c in r] for r in annotation])
                category_info = {'id': obj, 'is_crowd': None}
                annotation_info = PycocoCreatorTools.create_annotation_info(segmentation_id, image_id, category_info, binary_inst_mask)
                if annotation_info is not None:
                    coco_output["annotations"].append(annotation_info)
                segmentation_id = segmentation_id + 1
            image_id = image_id + 1
        return coco_output