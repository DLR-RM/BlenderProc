# Camera Depth of Field


<p align="center">
<img src="../../../images/camera_depth_of_field_rendering.jpg" alt="Front readme image" width=500>
</p>

In this example we are demonstrating the sampling features in relation to camera objects.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/camera_depth_of_field/main.py examples/resources/scene.obj examples/advanced/camera_depth_of_field/output
```

* `examples/advanced/camera_depth_of_field/main.py`: path to the main python file to run.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/advanced/camera_depth_of_field/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/advanced/camera_depth_of_field/output/0.hdf5
```

## Implementation

```python
# Create an empty object which will represent the cameras focus point
focus_point = bproc.object.create_empty("Camera Focus Point")
focus_point.set_location([0.5, -1.5, 3])

# Set the empty object as focus point and set fstop to regulate the sharpness of the scene
bproc.camera.add_depth_of_field(focus_point, fstop_value=0.25)
```
