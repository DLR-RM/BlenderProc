import numpy as np

from blenderproc.python.types.MeshObjectUtility import MeshObject, create_primitive


def generate_random_surface(surface_resolution: int = 1000, surface_size: float = 100) -> MeshObject:

    surface = create_primitive("PLANE")
    surface.set_scale([surface_size, surface_size, 0])
    surface.persist_transformation_into_mesh(scale=True)

    surface.subdivide_surface(number_of_cuts=surface_resolution)

    def random_distortion_size():
        return abs(np.random.normal(0.0, 1.5))

    def random_manipulation_size():
        if np.random.uniform(0, 1) < 0.8:
            return np.random.uniform(0.1, 8.0)
        else:
            return np.random.uniform(8.0, 20.0)

    surface.randomly_distort_surface_along_normals(distortion_values=random_distortion_size,
                                                   amount_of_distortions=800,
                                                   manipulation_sizes=random_manipulation_size)

    surface.add_modifier("SUBSURF", render_levels=2)
    surface.set_shading_mode("SMOOTH")

    return surface