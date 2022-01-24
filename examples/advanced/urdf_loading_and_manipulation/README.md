# URDF Robot Loading and Manipulation

---

<p align="center">
<img src="rendered_example.png" alt="Front readme image" width=400>
</p>

This example explains loading a robot from a urdf file and manipulating it.

## Usage

---

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/urdf_loading_and_manipulation/main.py /path/to/model.urdf examples/advanced/urdf_loading_and_manipulation/output
```

* `examples/advanced/urdf_loading_and_manipulation/main.py`: path to the python file with pipeline configuration.
* `/path/to/model.urdf`: path to a URDF robot model.
* `examples/advanced/urdf_loading_and_manipulation/output`: path to the output directory.

## Visualization

---

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
python scripts/visHdf5Files.py examples/advanced/urdf_loading_and_manipulation/output/*.hdf5
```

## Implementation

### Loading from an urdf file

```python
robot = bproc.loader.load_robot(urdf_file=args.urdf_file)
```

This will return a bproc.types.Robot instance.

### Basic functions of the Robot class

```python
robot.hide_irrelevant_objs()
robot.remove_link_by_index(index=0)
robot.set_ascending_category_ids()
```

The Robot class provides some basic functions which might come in handy. Here, we first hide all link, collision and inertial objects from rendering.
Then, we remove the first link as this often represents a transformation from world to base frame.
This automatically handles all respective parenting and transforms the child link to the current position.
Note that this would also allow us to shrink the robot by calling e.g. `robot.remove_link_by_index(5)` twice.
Depending on the relative transformations between the links this might not automatically produce a realistic representation.
Last but not least, we set ascending category ids to all links and their respective link objects.

### Rotation of links

```python
robot_matrix_world = []
for frame in range(9):
    for link in robot.links:
        if link.joint_type == "revolute":
            link.set_rotation_euler(rotation_euler=0.1, mode="relative", frame=frame)
    robot_matrix_world.append(robot.get_all_local2world_mats())
```

Here we relatively permute all revolute links of the robot by 0.1 radians per frame.
Depending on the constraints from the urdf file the rotation is only applied on one axis.
We additionally save the transformation matrices from each of the links to the world frame.

Note that since the robot class inherits from bpy.types.Entity, you can directly call `robot.set_location()` or
`robot.set_rotation_euler()` - this would manipulate the whole robot at once.

## Preparing URDF files

This example relies on [urdfpy](https://pypi.org/project/urdfpy/0.0.22/).
Currently (v0.0.22) you might need to format your `model.urdf` file:
- Mesh file paths can be saved with a prefix `mesh://` before the relative file name. Please replace this with the absolute (or relative) file name to the mesh.
- Instead of
```xml
<transmission name="..." type="...">
```
please write
```xml
<transmission name="...">
  <type>...</type>
```

Also note that blenderproc does not support all types of object loading (see [bpy.loader.load_obj()](blenderproc/python/loader/ObjectLoader.py)).
