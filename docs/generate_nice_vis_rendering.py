import os
import argparse
import glob
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.path.dirname(__file__), "../blenderproc/scripts"))
from saveAsImg import convert_hdf

if __name__ == "__main__":

    parser = argparse.ArgumentParser("Combines up to four images from .png or .hdf5. It requires a Color rendering.  Normal, distance and Semantic Segmentation are optional.")
    parser.add_argument("-f", "--file_path", nargs='*', help="File path to the list of color.png or .hdf5 file.", required=True)
    parser.add_argument("-o", "--output", help="Folder path where the resulting image/s should be saved.", type=str)
    parser.add_argument("-b", "--border", help="Adds a border around the images in white.", type=int, default=0)
    args = parser.parse_args()


    def convert_png_to_multiples(image_path, org_path):
        if "colors" in image_path:
            border = args.border
            normal_path = image_path.replace("colors", "normals")
            distance_path = image_path.replace("colors", "distance")
            depth_path = image_path.replace("colors", "depth")
            seg_path = image_path.replace("colors", "segmap")
            diffuse_path = image_path.replace("colors", "diffuse")
            used_imgs = []
            if os.path.exists(image_path):
                used_imgs.append(plt.imread(image_path))
            if os.path.exists(normal_path):
                used_imgs.append(plt.imread(normal_path))
            if os.path.exists(distance_path):
                used_imgs.append(plt.imread(distance_path))
            if os.path.exists(depth_path):
                used_imgs.append(plt.imread(depth_path))
            if os.path.exists(distance_path) and os.path.exists(depth_path):
                raise Exception("This can only work with one of the two, either distance or depth!")
            if os.path.exists(seg_path):
                used_imgs.append(plt.imread(seg_path))
            if os.path.exists(diffuse_path):
                used_imgs.append(plt.imread(diffuse_path))
            if used_imgs:
                img_size = used_imgs[0].shape
                if len(used_imgs) == 1:
                    final_img = np.ones((img_size[0] + border * 2, img_size[1] + border * 2, img_size[2]))
                elif len(used_imgs) == 2:
                    final_img = np.ones((img_size[0] * 2 + border * 3, img_size[1] + border * 2, img_size[2]))
                else:
                    final_img = np.ones((img_size[0] * 2 + border * 3, img_size[1] * 2 + border * 3, img_size[2]))

                final_img[border:img_size[0]+border, border:img_size[1]+border, :] = used_imgs[0]

                if len(used_imgs) == 2:
                    final_img[2 * border + img_size[0]:-border, border:border + img_size[1], :] = used_imgs[1]
                if len(used_imgs) == 3:
                    start_val = int((img_size[1] + border + border * 0.5) * 0.5)
                    final_img[border:img_size[0] + border, 2 * border + img_size[1]:-border, :] = used_imgs[1]
                    final_img[2 * border + img_size[0]:-border, start_val:start_val + img_size[1], :] = used_imgs[2]
                if len(used_imgs) == 4:
                    final_img[2 * border + img_size[0]:-border, border:border + img_size[1], :] = used_imgs[1]
                    final_img[border:img_size[0] + border, 2 * border + img_size[1]:-border, :] = used_imgs[2]
                    final_img[2 * border + img_size[0]:-border, 2 * border + img_size[1]:-border, :] = used_imgs[3]

            if ".png" in org_path:
                resulting_file_name = org_path.replace("colors", "rendering")
            else:
                if final_img.shape[2] == 3:
                    resulting_file_name = org_path.replace(".hdf5", "_rendering.jpg")
                elif final_img.shape[2] == 4:
                    if abs(np.min(final_img) - 1) < 1e-7:
                        final_img = final_img[:,:,:3]
                        resulting_file_name = org_path.replace(".hdf5", "_rendering.jpg")
                    else:
                        resulting_file_name = org_path.replace(".hdf5", "_rendering.png")
            if args.output:
                resulting_file_name = os.path.join(args.output, resulting_file_name)
            print("Saved in {}".format(resulting_file_name))
            plt.imsave(resulting_file_name, final_img)
            plt.close()
        else:
            raise Exception("The file path must point to the colors image: {}".format(image_path))

    if isinstance(args.file_path, str):
        file_paths = [args.file_path]
    elif isinstance(args.file_path, list):
        file_paths = args.file_path
    for file_path in file_paths:
        if os.path.exists(file_path):
            if file_path.endswith(".png"):
                convert_png_to_multiples(file_path, file_path)
            elif file_path.endswith(".hdf5"):
                if sys.platform != "win32":
                    tmp_path = "/dev/shm"
                    if not os.path.exists(tmp_path):
                        tmp_path = "/tmp/"
                else:
                    tmp_path = os.getenv("TEMP")
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
                    convert_png_to_multiples(color_img_path, file_path)
                for file in glob.glob(os.path.join(tmp_path, "*")):
                    os.remove(file)
                os.removedirs(tmp_path)
            else:
                raise Exception("This file format is not supported: {}".format(file_path))
        else:
            raise Exception("The given file does not exist: {}".format(args.file_path))




