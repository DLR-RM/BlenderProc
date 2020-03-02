# Replica dataset

This example introduces new tools for using replica dataset with BlenderProc.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/replica-dataset/config.yaml <path_to_the_replica_data_folder>  examples/replica-dataset/output
``` 

* `examples/replica-dataset/config.yaml`: path to the configuration file with pipeline configuration.
* `<path_to_the_replica_data_folder>`: Path to the replica dataset directory.
* `examples/replica-dataset/output`: path to the output directory.

## Steps

* Load replica room: `loader.ReplicaLoader` module.
* Extracts a floor in the room: `object.FloorExtractor` module.
* Samples multiples cameras in the room: `camera.ReplicaCameraSampler` module.
* Renders normals: `renderer.NormalRenderer` module.
* Writes output to .hdf5 container: `writer.Hdf5Writer` module.

## Config file

### Global

```yaml
"global": {
  "all": {
    "output_dir": "<args:1>",
    "data_set_name": "office_1",
    "data_path": "<args:0>"
  },
  "renderer": {
    "pixel_aspect_x": 1.333333333
  }
},
```

Note that `"data_set_name": "office_1"` is a replica room you want to render. This line can be replace with:
`"data_set_name": "<args:X>>"`, i.e. with an appropriate placeholder where `X` is a number of a placeholder.

### Replica loader

```yaml
{
  "module": "loader.ReplicaLoader",
  "config": {
    "use_smooth_shading": "True",
    "use_ambient_occlusion": "True"
  }
},
```

`loader.ReplicaLoader` handles importing objects from a given path. here we are using ambient occlusion to lighten up the scene, and enabling smooth shading on all surfaces, instead of flat shading.

### Floor extractor

```yaml
{
  "module": "object.FloorExtractor",
  "config": {
    "is_replica_object": "True",
    "obj_name": "mesh",
    "compare_angle_degrees" : 7.5, # max angle difference to up facing polygons
    "compare_height": 0.15  # height, which is allowed for polygons to be away from the height level in up and down dir.
  }
},
```

`object.FloorExtractor` searches for the specified object and splits the surfaces which point upwards at a specified level away.

### Replica camera sampler

```yaml
{
  "module": "camera.ReplicaCameraSampler",
  "config": {
    "is_replica_object": True,
    "cam_poses": [{
      "number_of_samples": 15,
      "clip_start": 0.01,
      "proximity_checks": {
        "min": 1.0,
        "avg": {
          "min": 2.0,
          "max": 4.0
        }
      },
      "location": [0, 0, 1.55],
      "rotation": {
        "value": {
          "provider":"sampler.Uniform3d",
          "max":[1.373401334, 0, 6.283185307],
          "min":[1.373401334, 0, 0]
        }
      },
    }]
  }
},
```

`camera.ReplicaCameraSampler` samples multiple camera poses per every imported room with camera-object collision check and obstacle check.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/replica-dataset/output/0.hdf5
```

## More examples

* [sung_basic](../suncg_basic): Rendering SUNCG scenes with fixed camera poses.
* [suncg_with_cam_sampling](../suncg_with_cam_sampling): Rendering SUNCG scenes with dynamically sampled camera poses.
