from blenderproc.python.SetupUtility import SetupUtility
SetupUtility.setup([])

from blenderproc.python.WriterUtility import WriterUtility
from blenderproc.python.Initializer import Initializer
from blenderproc.python.CameraUtility import CameraUtility
from blenderproc.python.types.LightUtility import Light
from blenderproc.python.MathUtility import MathUtility
from blenderproc.python.filter.Filter import Filter
from blenderproc.python.loader.BlendLoader import BlendLoader
from blenderproc.python.RendererUtility import RendererUtility

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('camera', nargs='?', default="examples/advanced/auto_shading/camera_position", help="Path to the camera file")
parser.add_argument('scene', nargs='?', default="examples/advanced/auto_shading/scene.blend", help="Path to the scene.obj file")
parser.add_argument('output_dir', nargs='?', default="examples/advanced/auto_shading/output", help="Path to where the final files, will be saved")
args = parser.parse_args()

Initializer.init()

# load the objects into the scene
objs = BlendLoader.load(args.scene)

# Change specular and roughness factor of all objects, so the shading will be better visible
for obj in objs:
    for mat in obj.get_materials():
        mat.set_principled_shader_value("Specular", 1)
        mat.set_principled_shader_value("Roughness", 0.3)

# Find the object with name "Sphere"
sphere = Filter.one_by_attr(objs, "name", "Sphere")
# Set it to AUTO shading, so all angles greater than 45 degrees will be shaded flat.
sphere.set_shading_mode("auto", 45)

# Find the object with name "Sphere.001"
other_sphere = Filter.one_by_attr(objs, "name", "Sphere.001")
# Set it to smooth shading, so all angles will be shaded flat.
other_sphere.set_shading_mode("smooth")

# define a light and set its location and energy level
light = Light()
light.set_type("POINT")
light.set_location([3, -8, 5])
light.set_energy(1000)

# define the camera intrinsics
CameraUtility.set_intrinsics_from_blender_params(1, 800, 600, lens_unit="FOV")

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position, euler_rotation = line[:3], line[3:6]
        matrix_world = MathUtility.build_transformation_mat(position, euler_rotation)
        CameraUtility.add_camera_pose(matrix_world)

# render the whole pipeline
data = RendererUtility.render()

# write the data to a .hdf5 container
WriterUtility.save_to_hdf5(args.output_dir, data)
