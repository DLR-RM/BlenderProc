# Object selection and manipulation

<p align="center">
<img src="../../../images/entity_manipulation_rendering.jpg" alt="Front readme image" width=400>
</p>

In this example we demonstrate how to select entities in the scene using `getter.Entity` and then manipulate them using the `EntityManipulator` module.

## Usage

Execute this in the BlenderProc main directory:

```
blenderproc run examples/basics/entity_manipulation/main.py examples/resources/scene.obj examples/basics/entity_manipulation/output
```

* `examples/basics/entity_manipulation/main.py`: path to the python file.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/basics/entity_manipulation/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/basics/entity_manipulation/output/0.hdf5
```

## Steps

### Entity manipulation

```python
# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)

# Find object with name Suzanne
suzanne = bproc.filter.one_by_attr(objs, "name", "Suzanne")
# Set its location and rotation
suzanne.set_location(np.random.uniform([0, 1, 2], [1, 2, 3]))
suzanne.set_rotation_euler([1, 1, 0])
```

The focus of this example is the filter operation and the setting of the rotation and location of objects with `blenderproc`.

Our condition in the filter operation is: `"name": 'Suzanne'`, which means that we want to select all the objects with `obj.name == 'Suzanne'`. In our case we have only one object which meets the requirement.
If we want more than just one element we could have used the `bproc.filter.by_attr()` fct. This way it is possible to select multiple objects.

NOTE: any given attribute_value of the type string can be treated as a *REGULAR EXPRESSION*, by setting `regex=True` in the `one_by_attr` fct. call. 
So `"name": 'Cylinder.*'` condition will select us all three cylinders in the scene.

For all possible `attribute_name`'s check the official blender documentation: https://docs.blender.org/api/current/bpy.types.Object.html.
