# Basic scene

<p align="center">
<img src="rendering_0.jpg" alt="Front readme image" width=375>
</p>

In this example we demonstrate a basic functionality of BlenderProc.

## Usage

Execute in the BlenderProc main directory, if this is the first time BlenderProc is executed. It will automatically
downloaded blender, see the config-file if you want to change the installation path:

```
python run.py examples/basic_object_pose/config.yaml examples/basic_object_pose/camera_positions examples/basic_object_pose/scene.obj examples/basic_object_pose/output
```

* `examples/basic_object_pose/config.yaml`: path to the configuration file with pipeline configuration.

The three arguments afterwards are used to fill placeholders like `<args:0>` inside this config file.
* `examples/basic_object_pose/camera_positions`: text file with parameters of camera pose.
* `examples/basic_object_pose/scene.obj`: path to the object file with the basic scene.
* `examples/basic_object_pose/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/basic_object_pose/output/0.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Selects objects and change their pose based on the condition: `manipulators.EntityManipulator` module.
* Creates a point light : `lighting.LightLoader` module.
* Loads camera positions from `camera_positions`: `camera.CameraLoader` module.
* Renders rgb, normals and distance: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

The only difference between this example and the basic example is that we change the object pose after we load it, and
we change some of the camera parameters.

### EntityManipulator

```yaml
    {
     "module": "manipulators.EntityManipulator",
      "config": {
        "selector": {
          "provider": "getter.Entity",
          "conditions": {
            "name" : "Suzanne",
            "type": "MESH"
          }
        },
        "matrix_world": [[0.9989916682243347, -0.03249780833721161, 0.0309765487909317, 0.14350244402885437],
        [-0.04397217929363251, -0.8474851250648499, 0.5289946794509888, -0.2128345370292663],
        [0.00906099658459425, -0.529823362827301, -0.8480595946311951, 5.43374633789062],
        [0.,0.,0.,1.]],
      },
    },
```

* Changes the object world matrix.

#### CameraLoader

```yaml
    {
      "module": "camera.CameraLoader",
      "config": {
        "path": "<args:0>",
        "file_format": "cam2world_matrix",
        "default_cam_param": {
          "cam_K": [650.018, 0, 637.962, 0, 650.018, 355.984, 0, 0 ,1],
          "resolution_x": 1280,
          "resolution_y": 720,
        }
      }
    },
```

* The camera pose is defined in a file whose path is again given via the command line (`examples/basic_object_pose/camera_positions` - contains 1 cam pose).
* The file format is the 16 values of the camera psoe 4x4 matrix, space separated.
* The `default_cam_param` is where we could optionally set the camera parameters e.g. intrinsics matrix "cam_K", fov, resolution.
* This module also writes the cam poses into extra `.npy` files located inside the `temp_dir` (default: /dev/shm/blender_proc_$pid). This is just some meta information, so we can later clearly say which image had been taken using which cam pose.

=> Creates the files `campose_0000.npy` and `campose_0001.npy` 

## More examples

* [camera_sampling](../camera_sampling): Introduction to sampling for cameras.
* [light_sampling](../light_sampling): Introduction to sampling for lights.
* [semantic_segmentation](../semantic_segmentation): Introduction to semantic segmentation
