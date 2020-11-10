# Basic scene

<p align="center">
<img src="rendering_0.jpg" alt="Front readme image" width=375>
</p>

In this example we demonstrate a basic functionality of BlenderProc.

## Usage

Execute in the BlenderProc main directory, if this is the first time BlenderProc is executed. It will automatically
downloaded blender, see the config-file if you want to change the installation path:

```
python run.py examples/basic_object_pose/config.yaml examples/basic_object_pose/obj_000004.ply examples/basic_object_pose/output
```

* `examples/basic_object_pose/config.yaml`: path to the configuration file with pipeline configuration.

The three arguments afterwards are used to fill placeholders like `<args:0>` inside this config file.
* `examples/basic_object_pose/obj_000004.ply`: path to the object file with a basic object from the `hb` dataset.
* `examples/basic_object_pose/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/basic_object_pose/output/0.hdf5
```

## Steps

* Loads `obj_00004.ply`: `loader.ObjectLoader` module.
* Selects objects and change their pose based on the condition: `manipulators.EntityManipulator` module.
* Creates a point light : `lighting.LightLoader` module.
* Loads camera positions from `camera_positions`: `camera.CameraLoader` module.
* Renders rgb, normals and distance: `renderer.RgbRenderer` module.
* Writes the data in `bop_dataset` format: `writer.BopWriter` module, this is explained in more details in the bop
  examples.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

The only difference between this example and the basic example is that we change the object pose after we load it, and
we change some of the camera parameters.

### ObjectLoader
```
    {
      "module": "loader.ObjectLoader",
      "config": {
        "path": "<args:0>", 
        "add_properties": {
            "cp_category_id": "1"
        }, 
      },
    },
```
* Load an object while adding custom properties to it, `category_id` is required for the `bop_writer` to run, further
  explination of the `bop_writer` and `bop` datasets are provided in the `bop` examples.

### EntityManipulator

```yaml
    {
      "module": "manipulators.EntityManipulator",
      "config": {
        "selector": {
          "provider": "getter.Entity",
          "conditions": {
            "type": "MESH"  # this guarantees that the object is a mesh, and not for example a camera
          }
        },
        "matrix_world":
            [[0.331458, -0.6064861, 0.7227108, 0],
            [-0.9415833, -0.2610635, 0.2127592, 0],
            [ 0.05963787, -0.7510136, -0.6575879, 0],
            [ -44.74526765165741, 89.70402424862098, 682.3395750305427, 1.0]],
      },
    },
```

* Changes the object world matrix.

#### CameraLoader

```yaml
    {
      "module": "camera.CameraLoader",
      "config": {
        "cam_poses": [
            "cam2world_matrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        ], 
        "source_frame": ["X", "-Y", "-Z"],
        "default_cam_param": {
          "cam_K": [537.4799, 0.0, 318.8965, 0.0, 536.1447, 238.3781, 0.0, 0.0, 1.0],
          "resolution_x": 640,
          "resolution_y": 480
        }
      }
    },
```

* The camera pose is defined by its world matrix, in this case it is just the identity.
* Change the camera source frame to match blender frame (this changes from OpenCV coordinate frame to blender's).
* The `default_cam_param` is where we could optionally set the camera parameters e.g. intrinsics matrix "cam_K", fov, resolution.
* This module also writes the cam poses into extra `.npy` files located inside the `temp_dir` (default: /dev/shm/blender_proc_$pid). This is just some meta information, so we can later clearly say which image had been taken using which cam pose.

=> Creates the files `campose_0000.npy` and `campose_0001.npy` 

## More examples

* [camera_sampling](../camera_sampling): Introduction to sampling for cameras.
* [light_sampling](../light_sampling): Introduction to sampling for lights.
* [semantic_segmentation](../semantic_segmentation): Introduction to semantic segmentation
