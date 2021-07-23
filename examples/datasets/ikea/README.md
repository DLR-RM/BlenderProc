# IKEA 
<p align="center">
<img src="rendered_example.png" alt="normals and color rendering of example table" width=300>
</p>

The focus of this example is the `loader.IKEALoader`, which can be used to load objects from the [IKEA dataset](http://ikea.csail.mit.edu/).
The IKEA dataset consists of 218 3D models of IKEA furniture collected from Google 3D Warehouse. <br>
If you use this dataset please cite

```
@article{lpt2013ikea,
   title={{Parsing IKEA Objects: Fine Pose Estimation}},
   author={Joseph J. Lim and Hamed Pirsiavash and Antonio Torralba},
   journal={ICCV},
   year={2013}
}
```

A script to download the .obj files is provided in the [scripts folder](../../scripts).

## Usage

Execute in the BlenderProc main directory:

```shell
python run.py examples/datasets/ikea/config.yaml <PATH_TO_IKEA> examples/datasets/ikea/output
``` 

* `examples/datasets/ikea/config.yaml`: path to the configuration file with pipeline configuration.
* `<PATH_TO_IKEA>`: path to the downloaded IKEA dataset, see the [scripts folder](../../scripts) for the download script. 
* `examples/datasets/ikea/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```shell
python scripts/visHdf5Files.py examples/datasets/ikea/output/*.hdf5
``` 

## Steps

* The IKEALoader loads all the object paths with the type and style specified in the config file.
* If there are multiple options it picks one randomly or if the style or the type is not specified it picks one randomly.
* The selected object is loaded.  
 

## Config file

### IKEALoader 

```yaml
{
    "module": "loader.IKEALoader",
    "config": {
      "data_dir": "<args:0>",
      "obj_type": "table",
      "obj_style": null,
    }
}
```
This module loads an IKEA Object, it only needs the path to the directory of the dataset, which is saved in `data_dir`. <br>
The `obj_type` = `table` means an object of type 'table' will be loaded. <br>
The `obj_style` = `null` means the object does not have to belong to a specific IKEA product series (e.g. HEMNES)

### CameraSampler

```yaml
{
    "module": "camera.CameraSampler",
    "config": {
     "cam_poses": [
     {
       "number_of_samples": 5,
       "location": {
         "provider":"sampler.PartSphere",
         "center": [0, 0, 20],
         "radius": 8,
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
