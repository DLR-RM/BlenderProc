import datetime
import numpy as np
from itertools import groupby
from skimage import measure
from PIL import Image

class PycocoCreatorTools:

    @staticmethod
    def bbox(img):
        rows = np.any(img, axis=1)
        cols = np.any(img, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        h = rmax - rmin
        w = cmax - cmin
        return [int(cmin), int(rmin), int(w), int(h)]
    
    @staticmethod
    def resize_binary_mask(array, new_size):
        image = Image.fromarray(array.astype(np.uint8)*255)
        image = image.resize(new_size)
        return np.asarray(image).astype(np.bool_)
    
    @staticmethod
    def close_contour(contour):
        if not np.array_equal(contour[0], contour[-1]):
            contour = np.vstack((contour, contour[0]))
        return contour
    
    @staticmethod
    def binary_mask_to_rle(binary_mask):
        rle = {'counts': [], 'size': list(binary_mask.shape)}
        counts = rle.get('counts')
        for i, (value, elements) in enumerate(groupby(binary_mask.ravel(order='F'))):
            if i == 0 and value == 1:
                    counts.append(0)
            counts.append(len(list(elements)))

        return rle
    
    @staticmethod
    def binary_mask_to_polygon(binary_mask, tolerance=0):
        """Converts a binary mask to COCO polygon representation
        Args:
            binary_mask: a 2D binary numpy array where '1's represent the object
            tolerance: Maximum distance from original points of polygon to approximated
                polygonal chain. If tolerance is 0, the original coordinate array is returned.
        """
        polygons = []
        # pad mask to close contours of shapes which start and end at an edge
        padded_binary_mask = np.pad(binary_mask, pad_width=1, mode='constant', constant_values=0)
        contours = measure.find_contours(padded_binary_mask, 0.5)
        contours = np.subtract(contours, 1)
        for contour in contours:
            contour = PycocoCreatorTools.close_contour(contour)
            contour = measure.approximate_polygon(contour, tolerance)
            if len(contour) < 3:
                continue
            contour = np.flip(contour, axis=1)
            segmentation = contour.ravel().tolist()
            # after padding and subtracting 1 we may get -0.5 points in our segmentation 
            segmentation = [0 if i < 0 else i for i in segmentation]
            polygons.append(segmentation)

        return polygons
    
    @staticmethod
    def create_image_info(image_id, file_name, image_size, 
                        date_captured=datetime.datetime.utcnow().isoformat(' '),
                        license_id=1, coco_url="", flickr_url=""):
        """Creates image info section of coco annotation
        Args:
            image_id: integer to uniquly identify image
            file_name: filename for image
        """
        image_info = {
                "id": image_id,
                "file_name": file_name,
                "width": image_size[0],
                "height": image_size[1],
                "date_captured": date_captured,
                "license": license_id,
                "coco_url": coco_url,
                "flickr_url": flickr_url
        }

        return image_info
    
    @staticmethod
    def create_annotation_info(annotation_id, image_id, category_info, binary_mask, 
                            image_size=None, tolerance=2, bounding_box=None):
        """Creates info section of coco annotation
        Args:
            annotation_id: integer to uniquly identify the annotation
            image_id: integer to uniquly identify image
            category_info: dict which contains category info and a boolean attribute "crowd" which tells if the annotation is a crowd of a class 
        """
        if image_size is not None:
            binary_mask = PycocoCreatorTools.resize_binary_mask(binary_mask, image_size)

        if bounding_box is None:
            bounding_box = PycocoCreatorTools.bbox(binary_mask)
            area = bounding_box[2] * bounding_box[3]

        if category_info["is_crowd"]:
            is_crowd = 1
            segmentation = PycocoCreatorTools.binary_mask_to_rle(binary_mask)
        else :
            is_crowd = 0
            segmentation = PycocoCreatorTools.binary_mask_to_polygon(binary_mask, tolerance)
            if not segmentation:
                return None

        annotation_info = {
            "id": annotation_id,
            "image_id": image_id,
            "category_id": category_info["id"],
            "iscrowd": is_crowd,
            "area": [area],
            "bbox": bounding_box,
            "segmentation": segmentation,
            "width": binary_mask.shape[1],
            "height": binary_mask.shape[0],
        }
        return annotation_info