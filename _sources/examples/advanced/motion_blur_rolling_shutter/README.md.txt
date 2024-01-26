# Motion Blur and Rolling Shutter

<p align="center">
<img src="../../../images/motion_blur_rolling_shutter_motion_blur.jpg" alt="Motion blur readme image" width=750>
<img src="../../../images/motion_blur_rolling_shutter_rolling_shutter.jpg" alt="Rolling Shutter readme image" width=750>
</p>

In this example we demonstrate how motion blur and a rolling shutter effect can be generated.

These effects are visible if either the camera or objects move between frames. The camera undergoes the following motion while the objects are stationary:

```
0 -10 4 1.3 0 0 # initial position
0 -15 4 1.3 0 0 # moving away from object
5 -15 4 1.3 0 0 # moving to the right
5 -15 8 1.3 0 0 # moving upwards
1 -11 5 1.3 0 0 # combined motion (to the left, towards object and downwards)
```

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/motion_blur_rolling_shutter/main_motion_blur.py examples/advanced/motion_blur_rolling_shutter/camera_positions examples/resources/scene.obj examples/advanced/motion_blur_rolling_shutter/output
```

* `examples/advanced/motion_blur_rolling_shutter/main_{motion_blur / rolling_shutter}.py`: path to the main python file to run.
* `examples/advanced/motion_blur_rolling_shutter/camera_positions`: text file with parameters of camera positions.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/advanced/motion_blur_rolling_shutter/output`: path to the output directory.

The python script `main_motion_blur.py` creates pure motion blur, the python `main_rolling_shutter.py` a rolling shutter effect together with a small amount of motion blur.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/advanced/motion_blur_rolling_shutter/output/0.hdf5
```

## Implementation

### Motion Blur

```python
# Enable motion blur
bproc.renderer.enable_motion_blur(motion_blur_length=0.5)
```

* `motion_blur_length` sets the time the shutter is open as fraction of the time between two frames. A value of `1` thus leaves the shutter open for the full time. The shutter opens half the `motion_blur_length` before the keyframe pose and closes half the time after.

### Rolling Shutter

```python
# Enable motion blur and rolling shutter
bproc.renderer.enable_motion_blur(
    motion_blur_length=0.8,
    rolling_shutter_type="TOP",
    rolling_shutter_length=0.05
)
```

* `rolling_shutter_length` sets the time one scanline is exposed as fraction of the `motion_blur_length`. If this value is set to `1`, no rolling shutter effect is created but just motion blur. If set to `0`, a pure rolling shutter effect is achieved.
