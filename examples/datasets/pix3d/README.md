# Pix3D 

<p align="center">
<img src="rendering.jpg" alt="Front readme image" width=300>
</p>

The focus of this example is the `loader.Pix3DLoader`, which can be used to load objects from the [Pix3D](http://pix3d.csail.mit.edu/) dataset.

We provide a script to download the .obj files, please see the scripts [folder](https://github.com/DLR-RM/BlenderProc/tree/master/scripts).

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/datasets/pix3d/config.yaml <PATH_TO_Pix3D> examples/datasets/pix3d/output
``` 

* `examples/datasets/pix3d/config.yaml`: path to the configuration file with pipeline configuration.
* `<PATH_TO_Pix3D>`: path to the downloaded pix3d dataset, get it [here](http://pix3d.csail.mit.edu/) 
* `examples/datasets/pix3d/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
python scripts/visHdf5Files.py examples/datasets/pix3d/output/*.hdf5
``` 

## Steps

* The Pix3DLoader loads all the object paths with the `category` = `bed`.
* One of them is now randomly selected and loaded 
 

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

### Pix3DLoader 

```yaml
{
    "module": "loader.Pix3DLoader",
    "config": {
      "data_path": "<args:0>",
      "used_category": "bed"
    }
}
```
This module loads a Pix3D Object, it only needs the path to the `Pix3D` folder, which is saved in `data_path`.
The `category` = `bed` means a random bed model will be loaded.

The position will be in the center of the scene.

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
