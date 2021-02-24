# BlenderKit 
<p align="center">
<img src="rendered_example.png" alt="normals, depth and color rendering of an example table" width=900>
</p>

The example demonstrates using `loader.BlendLoader` to load the .blend files downloaded from [BlenderKit](https://www.blenderkit.com/).

A script to download the .blend files is provided in the [scripts folder](../../scripts).

## Usage

Execute in the BlenderProc main directory:

```shell
python run.py examples/blenderkit/config.yaml <PATH_TO_.BLEND_FILE> examples/blenderkit/output
``` 

* `examples/blenderkit/config.yaml`: path to the configuration file with pipeline configuration.
* `<PATH_TO_.BLEND_FILE>`: path to the downloaded .blend file, see the [scripts folder](../../scripts) for the download script. 
* `examples/blenderkit/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```shell
python scripts/visHdf5Files.py examples/blenderkit/output/*.hdf5
``` 

## Steps

* The BlendLoader loads assets from blend file specified in the config file.

## Config file

### BlendLoader 

```yaml
{
    "module": "loader.BlendLoader",
    "config": {
      "path": "<args:0>"
    }
}
```
This module loads a BLEND file resource and needs the relative p[ath of the .blend file model you want to load, which should be specified under `path` attribute in the loader section above. <br>
Per default this will load all mesh objects from the given .blend file. By using the parameters `obj_types` and `datablocks`, also other data and object types can be loaded.

### CameraSampler

```yaml
{
    "module": "camera.CameraSampler",
    "config": {
     "cam_poses": [
     {
       "number_of_samples": 5,
       "location": {
         "provider": "sampler.PartSphere",
         "center": [0, 0, 0],
         "radius": 2.5,
         "part_sphere_vector": [1, 0, 0],
         "mode": "SURFACE"
       },
       "rotation": {
         "format": "look_at",
         "value": {
           "provider": "getter.POI"
         }
       }
     }
    ]}
}
```
For sampling camera poses we used the ``sampler.PartSphere`` which uses only the upper half of the sphere cut along the x-axis (defined by `part_sphere_vector`). 
The center of the sphere is moved in z-direction and camera positions are sampled from the upper hemisphere to ensure that their view is not "below" the object, which is specifically important for tables.   
Each camera rotation is computed to look directly at a sampled point of interest ``POI`` of the object, and the camera faces upwards in Z direction.
