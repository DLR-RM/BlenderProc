# ShapeNet 

<p align="center">
<img src="rendering.jpg" alt="Front readme image" width=1000>
</p>

The focus of this example is the `loader.ShapeNetLoader`, which can be used to load objects from the ShapeNet dataset.

See the [ShapeNet Webpage](http://www.shapenet.org/) for downloading the data. We cannot provide the script for downloading the ShapeNet dataset because a user account on the ShapeNet webpage is needed.

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

* Set the ShapeNet category as specified with `synset_id`: ```loader.ShapeNetLoader``` module.
* Set the ShapeNet category object as specified with `source_id`: ```loader.ShapeNetLoader``` module.
* Sample camera poses: ```camera.CameraSampler``` module.
* Render RGB, Depth and Normal images: ```renderer.RgbRenderer``` module.
* Write ShapeNet object data: ```writer.ShapeNetWriter``` module.
* Write Camera Pose and Instrinsics data: ```writer.CameraStateWriter``` module.
* Write HDF5 file: ```writer.Hdf5Writer``` module.

 
## Config file

### Global

```yaml
{
  "module": "main.Initializer",
  "config": {
    "global": {
      "output_dir": "<args:1>",
    }
  }
}
```

The same as in the basic example.

### ShapeNetLoader 

```yaml
{
  "module": "loader.ShapeNetLoader",
  "config": {
    "data_path": "<args:0>",
    "used_synset_id": "02691156",
    "used_source_id": "10155655850468db78d106ce0a280f87"
  }
}
```

* This module loads a ShapeNet Object, it only needs the path to the `ShapeNetCore.v2` folder, which is saved in `data_path`.
* The `used_synset_id` = `02691156` is set to the id of an airplane, and the `used_source_id` = `10155655850468db78d106ce0a280f87` selects one particular object of that category.
* The position will be in the center of the scene.


### CameraSampler

```yaml
{
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
}
```

We sample here five random camera poses, where the location is on a sphere with a radius of 2 around the object. 
Each cameras rotation is such that it looks directly at the object and the camera faces upwards in Z direction.


## RGB Renderer
```yaml
"module": "renderer.RgbRenderer",
"config": {
  "transparent_background": False,
  "render_normals": True,
  "samples": 350,
  "render_distance": True
}
```
To render with a transparent background, specify `transparent_background` as True. Depth and Normal images will also be produced.


## HDF5 Writer
```yaml
"module": "writer.Hdf5Writer",
"config": {
  "write_alpha_channel": False,
  "postprocessing_modules": {
    "distance": [
      {
        "module": "postprocessing.Dist2Depth",
        "config": {}
      }
    ]
  }
}
```
To write to a hdf5 file with a transparent image backgound, specify transparent_background as True. As the postprocessing step, `postprocessing.Dist2Depth` is applied in order to convert the distance image to an actual depth image.
