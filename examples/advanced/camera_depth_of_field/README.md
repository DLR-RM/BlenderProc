# Camera Depth of Field


<p align="center">
<img src="rendering.jpg" alt="Front readme image" width=500>
</p>

In this example we are demonstrating the sampling features in relation to camera objects.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/advanced/camera_depth_of_field/config.yaml examples/resources/scene.obj examples/advanced/camera_depth_of_field/output
```

* `examples/advanced/camera_depth_of_field/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/advanced/camera_depth_of_field/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/advanced/camera_depth_of_field/output/0.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light: `lighting.LightLoader` module.
* Create an empty plain axes, which is used as the focus point for the scene: `constructor.BasicEmptyInitializer` module
* Samples camera positions randomly above the plane looking at the point of interest. It also introduces a depth of field focused on the created plain axes: `camera.CameraSampler` module
* Renders rgb, normals and distance: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

### BasicEmptyInitializer

```yaml
{
  "module": "constructor.BasicEmptyInitializer",
  "config": {
    "empties_to_add": [
      {
        "type": "plain_axes",
        "name": "Camera Focus Point",
        "location": [0.5, -1.5, 3]
      }
    ]
  }
},
```

This module creates an empty object of type plain_axes. It does not have any mesh data and can not be seen in the final image, but we can use it as a focal point for the scene.

### Camera sampling & Depth of field

```yaml
{
  "module": "camera.CameraSampler",
  "config": {
    "intrinsics": {
      "fov": 1,
      "depth_of_field": {
        "fstop": 0.25,
        "focal_object": {
          "provider": "getter.Entity",
          "conditions": {
            "name": "Camera Focus Point"
          }
        }
      }
    },
    "cam_poses": [
      {
        "number_of_samples": 5,
        "location": {
          "provider":"sampler.PartSphere",
          "center": [0, 0, 0],
          "radius": 7,
          "mode": "SURFACE",
          "distance_above_center": 1.0,
        },
        "rotation": {
          "format": "look_at",
          "value": {
            "provider": "getter.POI"
          }
        }
      }
    ]
  }
}
```

The `camera.CameraSampler` module allows sampling camera positions and orientations. 
In this example, all camera poses are constrained to "look at" a point of interest (POI).

* Sample location uniformly on the surface of a part sphere, which has a radius of 7 and each valid point has to be at least 1.0 above the center of that sphere.
* Set orientation of the camera such that it will always look at the POI in any pose.
* Finally, we use the intrinsics to introduce a depth of field effect, by setting the fstop to 0.25 and the focal object to the newly generated `"Camera Focus Point"`

