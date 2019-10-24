# Basic SUNCG scene

![](output-summary.png)

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py examples/suncg_basic/config.yaml <path to cam_pose file> <path to house.json> examples/suncg_basic/output
```

The first argument should point to a file which describes one camera pose per line (here the output of `scn2cam` from the `SUNCGToolbox` can be used).
The second argument should contain the path to a house.json file which describes the scene that should be loaded.

## Steps

* Loads a SUNCG scene
* Loads camera positions from a given file
* Automatically adds light sources inside each room
* Renders color, normal, segmentation and a depth images
* Merges all into an `.hdf5` file

## Explanation of specific parts of the config file

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

* Next to setting the output directory for all modules, we also set the `pixel_aspect_x` parameter for all rendering modules. This is necessary to coincide with the aspect ratio assumed by the `scn2cam` script which generated the camera poses.  

### SuncgLoader
```yaml
{
  "name": "loader.SuncgLoader",
  "config": {
    "path": "<args:1>"
  }
},
```

* This loader automatically loads a SUNCG scene/house given the corresponding `house.json` file. 


### CameraLoader
```yaml
{
  "name": "camera.CameraLoader",
  "config": {
  "path": "<args:0>",
  "file_format": "location rotation _ _ _ fov _ _",
    "source_frame": ["X", "-Z", "Y"],
    "default_cam_param": {
      "rotation_format": "forward_vec",
      "fov_is_half": true
    }
  }
},
```

* Here the cam poses from the given file are loaded
* The `file_format` describes how each line should be parsed (Here we use the format used by files created by `scn2cam`; `_` denotes values which should be skipped)
* It's also necessary here to specify a different `source_frame`, as SUNCG does not use the same coordinate frame as Blender
* In `default_cam_param` we set parameters which should be set across all cam poses: We change the `rotation_format`. This is necessary as rotations are specified via a forward vector in the camera file. Also `fov_is_half` has to be activated, as SUNCG describes the FOV as the angle between forward vector and one side of the frustum, while blender assumes the FOV describes the angle between both sides of the frustum.

### SuncgLighting

```yaml
{
  "name": "lighting.SuncgLighting",
  "config": {}
},
```

* This module automatically sets light sources inside the loaded house. Therefore each window, lamp or lampshade gets an emissive material and also the ceiling is made to slowly emit light to make sure even rooms without lights or windows are not completely dark. 