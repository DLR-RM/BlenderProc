import datetime
import numpy as np
from skimage import measure


class CocoUtility:

    @staticmethod
    def generate_coco_annotations(segmentation_map_paths, image_paths, colormap, super_category_mapping, dataset_name, existing_coco_annotations=None):
        """Generates coco annotations for images

        :param segmentation_map_paths: A list of paths which points to the rendered segmentation maps.
        :param image_paths: A list of paths which points to the rendered segmentation maps.
        :param colormap: mapping for color, class and object
        :param super_category_mapping: A dict mapping object name to their corresponding supercategory (A supercategory can be a string which distinguishes objects belonging to different datasets)
        :param dataset_name: name of the dataset, a feature required by coco annotation format
        :param existing_coco_annotations: If given, the new coco annotations will be appended to the given coco annotations dict.
        :return: dict containing coco annotations
        """
        # Adds all objects from the color map to the coco output (skip background)
        categories = []
        for obj in colormap[1:]:
            categories.append({'id': int(obj["idx"]), 'name': obj["objname"], 'supercategory': super_category_mapping[obj["objname"]]})

        licenses = [{
            "id": 1,
            "name": "Attribution-NonCommercial-ShareAlike License",
            "url": "http://creativecommons.org/licenses/by-nc-sa/2.0/"
        }]
        info = {
            "description": dataset_name,
            "url": "https://github.com/waspinator/pycococreator",
            "version": "0.1.0",
            "year": 2020,
            "contributor": "Unknown",
            "date_created": datetime.datetime.utcnow().isoformat(' ')
        }

        images = []
        annotations = []

        for segmentation_map_path, image_path in zip(segmentation_map_paths, image_paths):
            segmentation_map = np.load(segmentation_map_path)

            # Add coco info for image
            image_id = len(images)
            images.append(CocoUtility.create_image_info(image_id, image_path, segmentation_map.shape))

            # Go through all objects visible in this image
            unique_objects = np.unique(segmentation_map)
            # Remove background
            unique_objects = np.delete(unique_objects, np.where(unique_objects == 0))
            for obj in unique_objects:
                # Calc object mask
                binary_inst_mask = np.where(segmentation_map == obj, 1, 0)
                # Add coco info for object in this image
                annotation = CocoUtility.create_annotation_info(len(annotations), image_id, int(obj), binary_inst_mask)
                if annotation is not None:
                    annotations.append(annotation)

        new_coco_annotations = {
            "info": info,
            "licenses": licenses,
            "categories": categories,
            "images": images,
            "annotations": annotations
        }

        if existing_coco_annotations is not None:
            new_coco_annotations = CocoUtility.merge_coco_annotations(existing_coco_annotations, new_coco_annotations)

        return new_coco_annotations

    @staticmethod
    def merge_coco_annotations(existing_coco_annotations, new_coco_annotations):
        """ Merges the two given coco annotation dicts into one.

        Currently this requires both coco annotations to have the exact same categories/objects.
        The "images" and "annotations" sections are concatenated and respective ids are adjusted.

        :param existing_coco_annotations: A dict describing the first coco annotations.
        :param new_coco_annotations: A dict describing the second coco annotations.
        :return: A dict containing the merged coco annotations.
        """
        if existing_coco_annotations["categories"] != new_coco_annotations["categories"]:
            raise NotImplementedError("The existing coco annotations file contains different categories/objects than the current scene. Merging the two lists is not implemented yet.")

        # Concatenate images sections
        image_id_offset = max([image["id"] for image in existing_coco_annotations["images"]]) + 1
        for image in new_coco_annotations["images"]:
            image["id"] += image_id_offset
        existing_coco_annotations["images"].extend(new_coco_annotations["images"])

        # Concatenate annotations sections
        annotation_id_offset = max([annotation["id"] for annotation in existing_coco_annotations["annotations"]]) + 1
        for annotation in new_coco_annotations["annotations"]:
            annotation["id"] += annotation_id_offset
            annotation["image_id"] += image_id_offset
        existing_coco_annotations["annotations"].extend(new_coco_annotations["annotations"])

        return existing_coco_annotations

    @staticmethod
    def create_image_info(image_id, file_name, image_size):
        """Creates image info section of coco annotation

        :param image_id: integer to uniquly identify image
        :param file_name: filename for image
        :param image_size: The size of the image, given as [W, H]
        """
        image_info = {
            "id": image_id,
            "file_name": file_name,
            "width": image_size[0],
            "height": image_size[1],
            "date_captured": datetime.datetime.utcnow().isoformat(' '),
            "license": 1,
            "coco_url": "",
            "flickr_url": ""
        }

        return image_info

    @staticmethod
    def create_annotation_info(annotation_id, image_id, object_id, binary_mask, tolerance=2):
        """Creates info section of coco annotation

        :param annotation_id: integer to uniquly identify the annotation
        :param image_id: integer to uniquly identify image
        :param object_id: The object id, should match with the object's category id
        :param binary_mask: A binary image mask of the object with the shape [H, W].
        :param tolerance: The tolerance for fitting polygons to the objects mask.
        """
        bounding_box = CocoUtility.bbox_from_binary_mask(binary_mask)
        area = bounding_box[2] * bounding_box[3]
        if area < 1:
            return None

        segmentation = CocoUtility.binary_mask_to_polygon(binary_mask, tolerance)

        annotation_info = {
            "id": annotation_id,
            "image_id": image_id,
            "category_id": object_id,
            "iscrowd": 0,
            "area": [area],
            "bbox": bounding_box,
            "segmentation": segmentation,
            "width": binary_mask.shape[1],
            "height": binary_mask.shape[0],
        }
        return annotation_info

    @staticmethod
    def bbox_from_binary_mask(binary_mask):
        """ Returns the smallest bounding box containing all pixels marked "1" in the given image mask.

        :param binary_mask: A binary image mask with the shape [H, W].
        :return: The bounding box represented as [x, y, width, height]
        """
        # Find all columns and rows that contain 1s
        rows = np.any(binary_mask, axis=1)
        cols = np.any(binary_mask, axis=0)
        # Find the min and max col/row index that contain 1s
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        # Calc height and width
        h = rmax - rmin
        w = cmax - cmin
        return [int(cmin), int(rmin), int(w), int(h)]

    @staticmethod
    def close_contour(contour):
        """ Makes sure the given contour is closed.

        :param contour: The contour to close.
        :return: The closed contour.
        """
        # If first != last point => add first point to end of contour to close it
        if not np.array_equal(contour[0], contour[-1]):
            contour = np.vstack((contour, contour[0]))
        return contour

    @staticmethod
    def binary_mask_to_polygon(binary_mask, tolerance=0):
        """Converts a binary mask to COCO polygon representation

         :param binary_mask: a 2D binary numpy array where '1's represent the object
         :param tolerance: Maximum distance from original points of polygon to approximated polygonal chain. If tolerance is 0, the original coordinate array is returned.
        """
        polygons = []
        # pad mask to close contours of shapes which start and end at an edge
        padded_binary_mask = np.pad(binary_mask, pad_width=1, mode='constant', constant_values=0)
        contours = np.array(measure.find_contours(padded_binary_mask, 0.5))
        # Reverse padding
        contours = contours - 1
        for contour in contours:
            # Make sure contour is closed
            contour = CocoUtility.close_contour(contour)
            # Approximate contour by polygon
            polygon = measure.approximate_polygon(contour, tolerance)
            # Skip invalid polygons
            if len(polygon) < 3:
                continue
            # Flip xy to yx point representation
            polygon = np.flip(polygon, axis=1)
            # Flatten
            polygon = polygon.ravel()
            # after padding and subtracting 1 we may get -0.5 points in our segmentation
            polygon[polygon < 0] = 0
            polygons.append(polygon.tolist())

        return polygons
