from src.main.Module import Module
from src.utility.CameraUtility import CameraUtility
from src.utility.LightUtility import Light
from src.utility.EntityUtility import Entity
from src.utility.ProviderUtility import get_all_mesh_objects, get_all_meshes_objects_with_name
from mathutils import Matrix, Vector, Euler

from src.utility.RendererUtility import RendererUtility


class Test(Module):

    def __init__(self, config):
        Module.__init__(self, config)

    def run(self):
        light = Light()
        light.set_type("POINT")
        light.set_location([5, -5, 5])
        light.set_energy(1000)

        CameraUtility.set_intrinsics_from_blender_params(1, 512, 512, lens_unit="FOV")
        with open(self.config.get_string("camera"), "r") as f:
            for line in f.readlines():
                line = [float(x) for x in line.split()]
                matrix_world = Matrix.Translation(Vector(line[:3])) @ Euler(line[3:6], 'XYZ').to_matrix().to_4x4()
                CameraUtility.add_camera_pose(matrix_world)

        objs = get_all_mesh_objects()

        objs = get_all_meshes_objects_with_name("Cube.*")
        print(objs)
        raise Exception("a")


        RendererUtility.init()
        RendererUtility.set_samples(350)
        RendererUtility.set_denoiser("INTEL")
        RendererUtility.enable_distance_output(self._determine_output_dir())
        RendererUtility.enable_normals_output(self._determine_output_dir())
        RendererUtility.render(self._determine_output_dir())
