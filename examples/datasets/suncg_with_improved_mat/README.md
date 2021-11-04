# SUNCG scene with improved materials 

<p align="center">
<img src="../../../images/readme.jpg" alt="Front readme image" width=430>
</p>

In contrast to the SUNCG basic example, we improve the materials loaded by SUNCG.
The procedure shown here could be done with every objects material as long as the material can be selected.

Furthermore, we do not load precomputed camera poses, but sample them.

This is an advanced example please check these example before:
* [sung_basic](../suncg_basic/README.md): More on rendering SUNCG scenes with fixed camera poses.
* [sung_with_cam_sampling](../suncg_with_cam_sampling/README.md): More on rendering SUNCG scenes with sampled camera poses.

## Usage

Execute in the BlenderProc main directory:

```
blenderpoc run examples/datasets/suncg_with_improved_mat/main.py <path to house.json> examples/datasets/suncg_with_improved_mat/output
```

* `examples/datasets/suncg_with_improved_mat/main.py`: path to the python file with pipeline configuration.
* `<path to house.json>`: Path to the house.json file of the SUNCG scene you want to render.
* `examples/datasets/suncg_with_improved_mat/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/datasets/suncg_with_improved_mat/output/0.hdf5
```

## Steps

* Loads a SUNCG scene.
* Sample camera positions inside every room.
* Automatically adds light sources inside each room.
* After that we change the materials three times, with different values.
* Writes sampled camera poses to file.
* Renders semantic segmentation map.
* Renders rgb, depth and normals.
* Merges all into an `.hdf5` file.

## Python file (main.py)

### MaterialManipulator

```python
# improve the materials, first use all materials and only filter the relevant materials out
all_materials = bproc.material.collect_all()
all_wood_materials = bproc.filter.by_attr(all_materials, "name", "wood.*|laminate.*|beam.*", regex=True)

# now change the used values
for material in all_wood_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.05, 0.5))
    material.set_principled_shader_value("Specular", np.random.uniform(0.5, 1.0))
    material.set_displacement_from_principled_shader_value("Base Color", np.random.uniform(0.001, 0.15))

all_stone_materials = bproc.filter.by_attr(all_materials, "name", "tile.*|brick.*|stone.*", regex=True)

# now change the used values
for material in all_stone_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.0, 0.2))
    material.set_principled_shader_value("Specular", np.random.uniform(0.9, 1.0))

all_floor_materials = bproc.filter.by_attr(all_materials, "name", "carpet.*|textile.*", regex=True)

# now change the used values
for material in all_floor_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.5, 1.0))
    material.set_principled_shader_value("Specular", np.random.uniform(0.1, 0.3))

```

This a quite complex call, that's why we will call through it from the top to the bottom.

```python
all_materials = bproc.material.collect_all()
all_wood_materials = bproc.filter.by_attr(all_materials, "name", "wood.*|laminate.*|beam.*", regex=True)
```
In this first part do we select all materials, which name start with wood, laminate or beam. 
All of those are in the Suncg dataset materials, which look like wood structures.
If you want to find out how your materials are named, click on the objects during debugging in blender and check their names.

```python
for material in all_wood_materials:
    material.set_principled_shader_value("Roughness", np.random.uniform(0.05, 0.5))
    material.set_principled_shader_value("Specular", np.random.uniform(0.5, 1.0))
    material.set_displacement_from_principled_shader_value("Base Color", np.random.uniform(0.001, 0.15))
```

This step is now repeated two times, with different values.
We first sample the `Roughness` of the material, with a uniform value sampler between `0.05` and `0.5`.
After that we repeat this process for the `Specular` sampling.
Check this page to understand the possible values better ([web link](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html#examples)).
You can set any of those values there, even overwrite the `"Base Color"`, which would remove any linked textures.

This last option adds displacement to your objects, so the object gets changed based on the color texture.
This means that a dark spot in the image dents the object inwards at that point and outwards if it is bright.
This make the surface more real looking as they do not look so flat. 

The depth rendering is not affected by this, the normal rendering is effected by this though.

Finally, the mode specifies if the same values are used for all materials or if each material gets its own values.
With `"once_for_each"` we decide that each object gets its own values.
