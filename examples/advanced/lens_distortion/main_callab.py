import blenderproc as bproc

import argparse

import numpy as np
from mathutils import Matrix

import os  # path

from skimage.feature import match_template
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('scene', help="Path to the scene.obj file, should be examples/resources/scene.obj")
parser.add_argument('config_file', help="Path to the camera calibration config file.")
parser.add_argument('output_dir',
                    help="Path to where the final files, will be saved, could be examples/basics/basic/output")
args = parser.parse_args()

bproc.init()

# load the objects into the scene
basename = os.path.basename(args.scene)
filename, file_extension = os.path.splitext(basename)
if file_extension == '.blend':
    objs = bproc.loader.load_blend(args.scene)
    obj = bproc.filter.one_by_attr(objs, "name", filename)
    obj.set_location([0, 0, 0])
    obj.set_rotation_euler([0, 0, 0])
elif file_extension == '.obj':
    objs = bproc.loader.load_obj(args.scene)
    objs[0].set_location([0, 0, 0])
    objs[0].set_rotation_euler([0, 0, 0])
else:
    raise Exception("The extension of the object file is neither .obj nor .blend .")

# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([0, 0, -1])
light.set_energy(30)

# setup the lens distortion and adapt intrinsics so that it can be later used in the PostProcessing
orig_res_x, orig_res_y, mapping_coords = bproc.camera.set_camera_parameters_from_config_file(args.config_file,
                                                                                             read_the_extrinsics=True)

# activate normal and distance rendering
bproc.renderer.enable_normals_output()
bproc.renderer.enable_distance_output(activate_antialiasing=True)

# render the whole pipeline
data = bproc.renderer.render()

# post process the data and apply the lens distortion
for key in ['colors', 'distance', 'normals']:
    # use_interpolation should be false, for everything except colors
    use_interpolation = key == "colors"
    data[key] = bproc.postprocessing.apply_lens_distortion(data[key], mapping_coords, orig_res_x, orig_res_y,
                                                           use_interpolation=use_interpolation)

# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)

# test: compare generated image with real image
if "img1" in os.path.basename(args.config_file):
    real_path = os.path.join("images", "lens_img1_real.png")
    norm_corr_limit = 0.660  # low since the real background is large and different
elif "img2" in os.path.basename(args.config_file):
    real_path = os.path.join("images", "lens_img2_real.png")
    norm_corr_limit = 0.890  # less background
else:
    raise Exception("Reference real image not found.")
img_gene = np.asarray(Image.fromarray(data['colors'][0]).convert('L'))
img_real = np.asarray(Image.open(real_path).convert('RGB').convert('L'))
assert img_gene.shape == img_real.shape
result = match_template(img_gene, img_real[3:-3, 3:-3], pad_input=False)
if result.argmax() == 24:  # center of the (7,7) correlation window
    print(f"The generated image is not biased w.r.t. the reference real image.")
    if result.max() > norm_corr_limit:
        print(f"The norm. correlation index between generated and real images is {np.round(result.max(), 3)}, "
              f"which is fine.")
    else:
        raise Exception("The norm. correlation index between generated and real image is too low. The images do "
                        "not match. Choose other object or config file.")
else:
    raise Exception("The generated calibration pattern image and the reference real image do not match. Choose other "
        f"object or config file: {result.argmax()}.")
