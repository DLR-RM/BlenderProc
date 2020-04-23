import os
import argparse
import glob
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from scripts.saveAsImg import convert_hdf

if __name__ == "__main__":

    parser = argparse.ArgumentParser("Combines four images from .png or .hdf5. Requires Color, Normal, Depth and Semantic Segmentation.")
    parser.add_argument("-f", "--file_path", help="File path to the color.png or .hdf5 file.", type=str, required=True)
    parser.add_argument("-o", "--output", help="File path where the resulting image should be saved.", type=str, required=True)
    parser.add_argument("-b", "--border", help="Adds a border around the images in white.", type=int, default=0)
    args = parser.parse_args()

    def convert_png_to_multiples(image_path):
        if "colors" in image_path:
            border = args.border
            color_img = plt.imread(image_path)
            img_size = color_img.shape
            final_img = np.ones((img_size[0] * 2 + border * 3, img_size[1] * 2 + border * 3, img_size[2]))
            normal_img = plt.imread(image_path.replace("colors", "normals"))
            depth_img = plt.imread(image_path.replace("colors", "depth"))
            final_img[border:img_size[0]+border, border:img_size[1]+border, :] = color_img

            seg_path = image_path.replace("colors", "segmap")
            if os.path.exists(seg_path):
                final_img[2*border+img_size[0]:-border, border:border+img_size[1], :] = normal_img
                semantic_img = plt.imread(image_path.replace("colors", "segmap"))
                final_img[2*border+img_size[0]:-border, 2*border+img_size[1]:-border, :] = depth_img
                final_img[border:img_size[0]+border, 2*border+img_size[1]:-border, :] = semantic_img
            else:
                final_img[border:border+img_size[0], 2*border+img_size[1]:-border, :] = normal_img
                start_val = int((img_size[1]+border+border*0.5)*0.5)
                final_img[2*border+img_size[0]:-border, start_val:start_val+depth_img.shape[1], :] = depth_img
            folder_name = os.path.dirname(os.path.abspath(args.output))
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            plt.imsave(args.output, final_img)
        else:
            raise Exception("The file path must point to the colors image: {}".format(image_path))

    if args.file_path and os.path.exists(args.file_path):
        file_path = args.file_path
        if file_path.endswith(".png"):
            convert_png_to_multiples(file_path)
        elif file_path.endswith(".hdf5"):
            tmp_path = "/dev/shm"
            if not os.path.exists(tmp_path):
                tmp_path = "/tmp/"
            tmp_path = os.path.join(tmp_path, "blender_proc_vis_gen_image")
            if os.path.exists(tmp_path):
                for file in glob.glob(os.path.join(tmp_path, "*")):
                    os.remove(file)
                os.removedirs(tmp_path)
                os.makedirs(tmp_path)
            else:
                os.makedirs(tmp_path)
            convert_hdf(file_path, tmp_path)
            color_img_path = os.path.join(tmp_path, os.path.basename(file_path).split(".")[0] + "_colors.png")
            if os.path.exists(color_img_path):
                convert_png_to_multiples(color_img_path)
            for file in glob.glob(os.path.join(tmp_path, "*")):
                os.remove(file)
            os.removedirs(tmp_path)
        else:
            raise Exception("This file format is not supported: {}".format(file_path))
    else:
        raise Exception("The given file does not exist: {}".format(args.file_path))





