# Motion Blur and Rolling Shutter

<p align="center">
<img src="motion_blur.png" alt="Motion blur readme image" width=750>
<img src="rolling_shutter.png" alt="Rolling Shutter readme image" width=750>
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
python run.py examples/advanced/motion_blur_rolling_shutter/config_motion_blur.yaml examples/advanced/motion_blur_rolling_shutter/camera_positions examples/resources/scene.obj examples/advanced/motion_blur_rolling_shutter/output
```

* `examples/advanced/motion_blur_rolling_shutter/config_{motion_blur / rolling_shutter}.yaml`: path to the configuration file with pipeline configuration.
* `examples/advanced/motion_blur_rolling_shutter/camera_positions`: text file with parameters of camera positions.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/advanced/motion_blur_rolling_shutter/output`: path to the output directory.

The configuration `config_motion_blur.yaml` creates pure motion blur, the configuration `config_rolling_shutter.yaml` a rolling shutter effect together with a small amount of motion blur.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/advanced/motion_blur_rolling_shutter/output/0.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light : `lighting.LightLoader` module.
* Loads camera positions from `camera_positions`: `camera.CameraLoader` module.
* Renders rgb, normals and distance: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

### RgbRenderer
```yaml
{
    "module": "renderer.RgbRenderer",
    "config": {
        "output_key": "colors",
        "samples": 350,
        "render_distance": True,
        "distance_output_key": "distance",
        "use_motion_blur" : True,
        "motion_blur_length" : 0.8,
        "use_rolling_shutter" : True,
        "rolling_shutter_length" : 0.05
      }
}
```

* `use_motion_blur` enables the motion blur feature of Blender used for motion blur and rolling shutter simulation.
* `motion_blur_length` sets the time the shutter is open as fraction of the time between two frames. A value of `1` thus leaves the shutter open for the full time. The shutter opens half the `motion_blur_length` before the keyframe pose and closes half the time after.
* `use_rolling_shutter` enables rolling shutter simulation. Rows are exposed from top to bottom. `use_motion_blur` has to be activated and `motion_blur_length` set to a value bigger than `0`.
* `rolling_shutter_length` sets the time one scanline is exposed as fraction of the `motion_blur_length`. If this value is set to `1`, no rolling shutter effect is created but just motion blur. If set to `0`, a pure rolling shutter effect is achieved.
