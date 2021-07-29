from src.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from src.utility.postprocessing.StereoGlobalMatching import StereoGlobalMatching
from src.utility.Utility import Utility
from src.utility.MathUtility import MathUtility
from src.utility.CameraUtility import CameraUtility
from src.utility.LabelIdMapping import LabelIdMapping
from src.utility.MaterialLoaderUtility import MaterialLoaderUtility
from src.utility.loader.SuncgLoader import SuncgLoader
from src.utility.lighting.SuncgLighting import SuncgLighting
from src.utility.WriterUtility import WriterUtility
from src.utility.Initializer import Initializer
from src.utility.RendererUtility import RendererUtility

import argparse
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('camera', help="Path to the camera file which describes one camera pose per line, here the output of scn2cam from the SUNCGToolbox can be used")
parser.add_argument('house', help="Path to the house.json file of the SUNCG scene to load")
parser.add_argument('output_dir', nargs='?', default="examples/datasets/suncg_basic/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
label_mapping = LabelIdMapping.from_csv(Utility.resolve_path(os.path.join('resources', 'id_mappings', 'nyu_idset.csv')))
objs = SuncgLoader.load(args.house, label_mapping=label_mapping)

# define the camera intrinsics
K = np.array([
    [650.018, 0, 637.962],
    [0, 650.018, 355.984],
    [0, 0, 1]
])
CameraUtility.set_intrinsics_from_K_matrix(K, 1280, 720)
CameraUtility.set_stereo_parameters(interocular_distance=0.05, convergence_mode="PARALLEL", convergence_distance=0.00001)

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position = MathUtility.change_coordinate_frame_of_point(line[:3], ["X", "-Z", "Y"])
        rotation = MathUtility.change_coordinate_frame_of_point(line[3:6], ["X", "-Z", "Y"])
        matrix_world = MathUtility.build_transformation_mat(position, CameraUtility.rotation_from_forward_vec(rotation))
        CameraUtility.add_camera_pose(matrix_world)

# makes Suncg objects emit light
SuncgLighting.light()

# activate normal and distance rendering
RendererUtility.enable_distance_output()
MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=True)
RendererUtility.toggle_stereo(True)

# render the whole pipeline
data = RendererUtility.render()

data["stereo-depth"], data["disparity"] = StereoGlobalMatching.match(data["colors"], disparity_filter=False)

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
