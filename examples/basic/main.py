from src.utility.SetupUtility import SetupUtility
SetupUtility.setup(["h5py"])

from src.utility.Initializer import Initializer
from src.utility.loader.ObjectLoader import ObjectLoader
from src.utility.CameraUtility import CameraUtility
from src.utility.LightUtility import Light
from mathutils import Matrix, Vector, Euler

from src.utility.RendererUtility import RendererUtility

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('camera')
parser.add_argument('scene')
parser.add_argument('output')
args = parser.parse_args()

Initializer.init()

objs = ObjectLoader.load(args.scene)

light = Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)

CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        matrix_world = Matrix.Translation(Vector(line[:3])) @ Euler(line[3:6], 'XYZ').to_matrix().to_4x4()
        CameraUtility.add_camera_pose(matrix_world)

RendererUtility.init()
RendererUtility.toggle_auto_tile_size(True)
RendererUtility.set_samples(350)
RendererUtility.set_denoiser("INTEL")
RendererUtility.enable_distance_output(args.output)
RendererUtility.enable_normals_output(args.output)
RendererUtility.render(args.output)