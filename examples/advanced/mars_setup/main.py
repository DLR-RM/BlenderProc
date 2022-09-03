import blenderproc as bproc

import random
import numpy as np


bproc.init()
bproc.object.create_primitive("MONKEY")
bproc.world.add_dynamic_sky_as_world_background(scene_brightness=1.0, sky_color=[0.7, 0.11, 0.019, 1.0],
                                                horizon_color=[0.3, 0.08, 0.06, 1.0],
                                                sun_direction=(-0.0744048, -0.741071, 0.667291))

cubes = [bproc.object.create_primitive("MONKEY") for i in range(15)]
for cube in cubes:
    cube.set_scale([random.uniform(0.01, 0.05)] * 3)
    mat = bproc.material.create("New")
    mat.set_principled_shader_value("Base Color", np.random.uniform(0, 1, 3).tolist() + [1])
    cube.add_material(mat)

plane = bproc.object.generate_random_surface()
plane.add_particle_system(cubes, amount_of_particles=4000, children_clumping_factor=-0.1)

for cube in cubes:
    cube.delete(remove_all_offspring=True)