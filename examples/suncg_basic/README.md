# Basic SUNCG scene

![](output-summary.png)

Renders a SUNCG scene using precomputed camera poses read from file.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/suncg_basic/config.yaml <path to cam_pose file> <path to house.json> examples/suncg_basic/output
```

* `examples/suncg_basic/config.yaml`: path to the configuration file with pipeline configuration.
* `<path to cam_pose file>`: Should point to a file which describes one camera pose per line (here the output of `scn2cam` from the `SUNCGToolbox` can be used).
* `<path to house.json>`: Path to the house.json file of the SUNCG scene you want to render.
* `examples/suncg_basic/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/suncg_basic/output/0.hdf5
```

## Steps

* Loads a SUNCG scene: `loader.SuncgLoader` module.
* Loads camera positions from a given file: `camera.CameraLoader` module.
* Automatically adds light sources inside each room: `lighting.SuncgLighting` module.
* Renders normals: `renderer.NormalRenderer` module.
* Renders semantic segmentation map: `renderer.SegMapRenderer` module.
* Renders rgb and depth: `renderer.RgbRenderer` module.
* Merges all into an `.hdf5` file: `writer.Hdf5Writer` module.

## Config file

### Global settings

```yaml
"global": {
  "all": {
    "output_dir": "<args:2>"
  },
  "renderer": {
    "pixel_aspect_x": 1.333333333
  }
},
```

Next to setting the output directory for all modules, we also set the `pixel_aspect_x` parameter for all rendering modules.
This is necessary to coincide with the aspect ratio assumed by the `scn2cam` script which generated the camera poses.  

### SuncgLoader

```yaml
{
  "module": "loader.SuncgLoader",
  "config": {
    "path": "<args:1>"
  }
},
```

This loader automatically loads a SUNCG scene/house given the corresponding `house.json` file. 
Therefore all objects specified in the given `house.json` file are imported and textured.
The `SuncgLoader` also sets the `category_id` of each object, such that semantic segmentation maps can be rendered in a following step.

### CameraLoader

```yaml
{
  "module": "camera.CameraLoader",
  "config": {
    "path": "<args:0>",
    "file_format": "location rotation/value _ _ _ fov _ _",
    "source_frame": ["X", "-Z", "Y"],
    "default_cam_param": {
      "rotation": {
        "format": "forward_vec"
      }
      "fov_is_half": true
    }
  }
},
```

Here the cam poses from the given file are loaded. 
This text based file describes one camera pose per line.
The `file_format` describes how each line should be parsed (Here we use the format used by files created by `scn2cam`; `_` denotes values which should be skipped).

It's also necessary here to specify a different `source_frame`, as `scn2cam` does not use the same coordinate frame as Blender.

In `default_cam_param` we set parameters which are the same across all cam poses: 
We change the `rotation/format`. This is necessary as rotations are specified via a forward vector in the camera file. 
Also `fov_is_half` has to be activated, as SUNCG describes the FOV as the angle between forward vector and one side of the frustum, while blender assumes the FOV describes the angle between both sides of the frustum.

### SuncgLighting

```yaml
{
  "module": "lighting.SuncgLighting",
  "config": {}
},
```

This module automatically sets light sources inside the loaded house.
Therefore each window, lamp or lampshade gets an emissive material and also the ceiling is made to slowly emit light to make sure even rooms without lights or windows are not completely dark.


## More examples

* [suncg_with_cam_sampling](../suncg_with_cam_sampling): More on rendering SUNCG scenes with dynamically sampled camera poses.
