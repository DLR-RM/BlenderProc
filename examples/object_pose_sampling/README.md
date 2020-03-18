# Object pose sampling

![](rendering.png)

The focus of this example is introducing the `object.ObjectPoseSampler` which allows one to sample object poses inside a sampling volume with collision checks.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/object_pose_sampling/config.yaml examples/object_pose_sampling/camera_positions examples/object_pose_sampling/scene.obj examples/object_pose_sampling/output
``` 

* `examples/object_pose_sampling/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/object_pose_sampling/camera_positions`: text file with parameters of camera positions.
* `examples/object_poses_sampling/scene.obj`: path to the object file with the basic scene.
* `examples/object_pose_sampling/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/object_pose_sampling/output/0.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light : `lighting.LightLoader` module.
* Loads camera positions from `camera_positions`: `camera.CameraLoader` module.
* Sample object poses: `object.ObjectPoseSampler` module.
* Renders normals: `renderer.NormalRenderer` module.
* Renders rgb: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

### Object pose Sampling

```yaml
{
  "module": "object.ObjectPoseSampler",
  "config":{
    "max_iterations": 1000,
    "objects_to_sample": {
      "provider": "getter.Entity",
      "condition": {
        "sample_pose": True 
      }
    },
    "pos_sampler":{
      "provider": "sampler.Uniform3d",
      "max": [5,5,5],
      "min": [-5,-5,-5]
    },
    "rot_sampler": {
      "provider": "sampler.Uniform3d",
      "max": [0,0,0],
      "min": [6.28,6.28,6.28]
    }
  }
},
```
 
`object.ObjectPoseSampler` for each `passive` object in the scene places the object outside the sampling volume until there are objects remaining and `max_iterations` have not been reached, point is sampled.
Then the object is placed at the sampled point with collision check. If there is a collision - the position is reset and module tries to sample a new one.
Here we are sampling location and rotation using `sampler.Uniform3d` provider.

## More examples

* [camera_sampling](../camera_sampling): Introduction to sampling for cameras.
* [light_sampling](../light_sampling): Introduction to sampling for lights.
* [entity_manipulation](../entity_manipulation): More on the true power of Providers.
