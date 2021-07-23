# Camera Object Pose Setting

<p align="center">
<img src="rendering_0.jpg" alt="Front readme image" width=375>
<img src="hb_val_3_0.png" alt="Front readme image" width=375>
</p>

In this example we show how to load and render a 3D model in specified extrinsics and intrinsics with BlenderProc.

## Usage

Execute in the BlenderProc main directory, if this is the first time BlenderProc is executed. It will automatically
downloaded blender, see the config-file if you want to change the installation path:

```
python run.py examples/basics/camera_object_pose/config.yaml examples/basics/camera_object_pose/obj_000004.ply examples/basics/camera_object_pose/output
```

* `examples/basics/camera_object_pose/config.yaml`: path to the configuration file with pipeline configuration.

The arguments afterwards are used to fill placeholders like `<args:0>` inside this config file.
* `examples/basics/camera_object_pose/obj_000004.ply`: path to the model file, here a basic object from the `hb` dataset.
* `examples/basics/camera_object_pose/output`: path to the output directory.

## Steps

* Loads `obj_00004.ply`: `loader.ObjectLoader` module.
* Selects objects and change their pose based on the condition: `manipulators.EntityManipulator` module.
* Creates a point light : `lighting.LightLoader` module.
* Loads camera positions: `camera.CameraLoader` module.
* Sets vertex colors as material: `manipulators.MaterialManipulator` module.
* Renders rgb and distance: `renderer.RgbRenderer` module.
* Writes data, intrinsics and extrinsics in `bop_dataset` format: `writer.BopWriter` module, this is explained in more details in the bop
  examples.

## Config file


### ObjectLoader

```yaml
    {
      "module": "loader.ObjectLoader",
      "config": {
        "path": "<args:0>", 
        "add_properties": {
            "cp_category_id": "1"
        }, 
      },
    }
```
* Loads an object and adds a custom property `category_id`. This is required by the `bop_writer` to write object poses in `bop_format`.

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
            [[0.331458, -0.9415833, 0.05963787, -0.04474526765165741],
             [-0.6064861, -0.2610635, -0.7510136, 0.08970402424862098],
             [0.7227108, 0.2127592, -0.6575879, 0.6823395750305427],
             [0, 0, 0, 1.0]],
        "scale": [0.001, 0.001, 0.001] # Scale 3D model from mm to m
      },
    }
```

* Set the object pose `matrix_world` in meter  
* `scale` the original model from mm to meter in every dimension. Note: Remove when object is already in meter! 

#### CameraLoader

```yaml
    {
      "module": "camera.CameraLoader",
      "config": {
        "source_frame": ["X", "-Y", "-Z"],
        "cam_poses": [
            "cam2world_matrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        ], 
        "default_cam_param": {
          "cam_K": [537.4799, 0.0, 318.8965, 0.0, 536.1447, 238.3781, 0.0, 0.0, 1.0],
          "resolution_x": 640,
          "resolution_y": 480
        }
      }
    }
```

* The camera pose is defined by its world matrix, in this case it is just the identity.
* Change the camera source frame to match blender frame (this changes from OpenCV coordinate frame to blender's).
* The `default_cam_param` is where we can set the camera parameters e.g. intrinsics matrix "cam_K", fov, resolution.
* This module also writes the cam poses into extra `.npy` files located inside the `temp_dir` (default: /dev/shm/blender_proc_$pid). 

#### Material Manipulator
```yaml
    {
      "module": "manipulators.MaterialManipulator",
      "config": {
        "selector": {
          "provider": "getter.Material",
          "conditions": {
            "name": "ply_material"
          }
        },
        "cf_change_to_vertex_color": "Col"
      }
    }
```
* Required to render vertex colors defined in ply file

#### Bop Writer

```yaml
    {
      "module": "writer.BopWriter",
      "config": {
        "m2mm": True,
        "append_to_existing_output": True,
        "postprocessing_modules": {
          "distance": [
            {"module": "postprocessing.Dist2Depth"}
          ]
        }
      }
    }
```

* Saves all pose and camera information that is provided in BOP datasets.
* `"m2mm"` (default=True) converts the pose to mm as in the original bop annotations. Set to False if you want it in meters.
* `"append_to_existing_output"` means that if the same output folder is chosen, data will be accumulated and not overwritten
* `postprocessing.Dist2Depth` to convert the distance images from Blender to actual depth images.
