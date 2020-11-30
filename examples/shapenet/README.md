# ShapeNet 

<p align="center">
<img src="rendering.jpg" alt="Front readme image" width=300>
</p>

The focus of this example is the `loader.ShapeNetLoader`, which can be used to load objects from the ShapeNet dataset.

See [the shape net weg page](http://www.shapenet.org/) for downloading the data, we can not provide a script for downloading as you have to have an account to download the data.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/shapenet/config.yaml <PATH_TO_ShapeNetCore.v2> examples/shapenet/output
``` 

* `examples/shapenet/config.yaml`: path to the configuration file with pipeline configuration.
* `<PATH_TO_ShapeNetCore.v2>`: path to the downloaded shape net core v2 dataset, get it [here](http://www.shapenet.org/) 
* `examples/shapenet/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
python scripts/visHdf5Files.py examples/shapenet/output/*.hdf5
``` 

## Steps

* The ShapeNetLoader loads all the object paths with the `synset_id` = `02801938`, this id stands for the category `basket`.
* One of them is now randomly selected and loaded 
 

## Config file

### Global

```yaml
"module": "main.Initializer",
"config": {
  "global": {
    "output_dir": "<args:1>",
  }
}
```

The same as in the basic example.

### ShapeNetLoader 

```yaml
"module": "loader.ShapeNetLoader",
"config": {
  "data_path": "<args:0>",
  "used_synset_id": "02801938"
}
```
This module loads a ShapeNet Object, it only needs the path to the `ShapeNetCore.v2` folder, which is saved in `data_path`.
The `synset_id` = `02801938` is set to the id of a basket, which means a random basket will be loaded.

The position will be in the center of the scene.

### CameraSampler

```yaml
"module": "camera.CameraSampler",
"config": {
  "cam_poses": [
    {
      "number_of_samples": 5,
      "location": {
        "provider":"sampler.Sphere",
        "center": [0, 0, 0],
        "radius": 2,
        "mode": "SURFACE"
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
```

We sample here five random camera poses, where the location is on a sphere with a radius of 2 around the object. 
Each cameras rotation is such that it looks directly at the object and the camera faces upwards in Z direction.


## RGB Renderer
```
"module": "renderer.RgbRenderer",
  "config": {
    "transparent_background": False,
    "render_normals": True,
    "samples": 350,
    "render_distance": true
  }
}
```
To render with a transparent background, specify `transparent_background` as True. 


## HDF5 Writer
```
"module": "writer.Hdf5Writer",
    "config": {
    "write_alpha_channel": False,
    "postprocessing_modules": {
      "distance": [
        {
          "module": "postprocessing.TrimRedundantChannels",
          "config": {}
        }
      ]
    }
}
```
To write to a hdf5 file with a transparent image backgound, specify transparent_background as True.

## More examples

* [sung_basic](../suncg_basic): More on rendering SUNCG scenes with fixed camera poses.
* [suncg_with_cam_sampling](../suncg_with_cam_sampling): More on rendering SUNCG scenes with dynamically sampled camera poses.
