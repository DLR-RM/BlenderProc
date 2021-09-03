from blenderproc.utility.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.utility.Utility import Utility
from blenderproc.utility.MathUtility import MathUtility
from blenderproc.utility.CameraUtility import CameraUtility
from blenderproc.utility.LabelIdMapping import LabelIdMapping
from blenderproc.utility.MaterialLoaderUtility import MaterialLoaderUtility
from blenderproc.utility.SegMapRendererUtility import SegMapRendererUtility
from blenderproc.utility.loader.SuncgLoader import SuncgLoader
from blenderproc.utility.lighting.SuncgLighting import SuncgLighting
from blenderproc.utility.WriterUtility import WriterUtility
from blenderproc.utility.Initializer import Initializer
from blenderproc.utility.RendererUtility import RendererUtility

import argparse
import os

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
CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, pixel_aspect_x=1.333333333, lens_unit="FOV")

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
RendererUtility.enable_normals_output()
RendererUtility.enable_distance_output()
MaterialLoaderUtility.add_alpha_channel_to_textures(blurry_edges=True)

# render the whole pipeline
data = RendererUtility.render()

data.update(SegMapRendererUtility.render(Utility.get_temporary_directory(), Utility.get_temporary_directory(), "class", use_alpha_channel=True))

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
