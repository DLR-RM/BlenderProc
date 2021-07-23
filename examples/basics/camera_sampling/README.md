# Camera sampling


<p align="center">
<img src="rendering_0.png" alt="Front readme image" width=375>
<img src="rendering_1.jpg" alt="Front readme image" width=375>
<img src="rendering_1.jpg" alt="Front readme image" width=375>
</p>

In this example we are demonstrating the sampling features in relation to camera objects.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/basics/camera_sampling/config.yaml examples/resources/scene.obj examples/basics/camera_sampling/output
```

* `examples/basics/camera_sampling/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/basics/camera_sampling/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/basics/camera_sampling/output/0.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light: `lighting.LightLoader` module.
* Samples camera positions randomly above the plane looking to the point of interest: `camera.CameraSampler` module.
* Renders rgb, normals and distance: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

### Camera sampling

```yaml
{
  "module": "camera.CameraSampler",
  "config": {
    "cam_poses": [
      {
        "number_of_samples": 5,
        "location": {
          "provider":"sampler.Uniform3d",
          "max":[10, 10, 8],
          "min":[-10, -10, 12]
        },
        "rotation": {
          "format": "look_at",
          "value": {
            "provider": "getter.POI"
          },
          "inplane_rot": {
            "provider": "sampler.Value",
            "type": "float",
            "min": -0.7854,
            "max": 0.7854
          }
        }
      }
    ]
  }
}
```

The `camera.CameraSampler` module allows sampling camera positions and orientations. 
In this example, all camera poses are constrained to "look at" a point of interest (POI).

* Sample location uniformly in a bounding box above the plane.

For sampling camera positions we are using the [sampler.Uniform3d](../../src/provider/sampler) Provider. To call a sampler for some attribute of a camera, specify a name (`provider`) of a desired sampler and define some input arguments for it, e.g. `min` and `max`.
The sampler returns a value based on these input parameters specified in the config file, check the documentation for the samplers for more information on the input arguments, output formats, etc.

* Set orientation of the camera such that it will always look at the POI in any pose. 

The [getter.POI](../../src/provider/getter) Provider also has a well-defined config structure, but here its output is fully dependent on the current state of the objects in the scene. The POI per default is defined as the object position closest to the mean position of all objects. 

* Optionally, add an `"inplane_rot"` sampler to rotate the camera around the optical axis
It samples float values between specified `min` and `max` in radians. Here it is used to randomly inplane rotate the cameras in an interval of +/- 45 degree.
