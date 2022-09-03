import blenderproc as bproc

import random
import numpy as np


bproc.init()

cubes = [bproc.object.create_primitive("MONKEY") for i in range(15)]
for cube in cubes:
    cube.set_scale([random.uniform(0.01, 0.05)] * 3)
    mat = bproc.material.create("New")
    mat.set_principled_shader_value("Base Color", np.random.uniform(0, 1, 3).tolist() + [1])
    cube.add_material(mat)

plane = bproc.object.generate_random_surface()
plane.add_particle_system(cubes, amount_of_particles=100, children_clumping_factor=-0.1)

for cube in cubes:
    cube.delete(remove_all_offspring=True)