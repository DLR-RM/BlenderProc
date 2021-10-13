# Pix3D 

<p align="center">
<img src="../../../images/pix3d_rendering.jpg" alt="Front readme image" width=300>
</p>

The focus of this example is the `bproc.loader.load_pix3d()`, which can be used to load objects from the [Pix3D](http://pix3d.csail.mit.edu/) dataset.

We provide a script to download the .obj files, please see the scripts [folder](https://github.com/DLR-RM/BlenderProc/tree/master/scripts).

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/datasets/pix3d/main.py <PATH_TO_Pix3D> examples/datasets/pix3d/output
``` 

* `examples/datasets/pix3d/main.py`: path to the python file with pipeline configuration.
* `<PATH_TO_Pix3D>`: path to the downloaded pix3d dataset, get it [here](http://pix3d.csail.mit.edu/) 
* `examples/datasets/pix3d/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
blenderproc vis hdf5 examples/datasets/pix3d/output/*.hdf5
``` 

## Steps

* The Pix3DLoader loads all the object paths with the `category` = `bed`.
* One of them is now randomly selected and loaded 
 

## Python file (main.py)

### Pix3DLoader 

```python
# Load Pix3D objects from type table into the scene
objs = bproc.loader.load_pix3d(data_path=args.pix_path, used_category="bed")
```
This loads a Pix3D Object, it only needs the path to the `Pix3D` folder, which is saved in `args.pix_path`.
The `used_category` = `bed` means a random bed model will be loaded.

The position will be in the center of the scene.

### CameraSampler

```python
# Find point of interest, all cam poses should look towards it
poi = bproc.object.compute_poi(objs)
# Sample five camera poses
for i in range(5):
    # Sample random camera location around the object
    location = bproc.sampler.sphere([0, 0, 0], radius=2, mode="SURFACE")
    # Compute rotation based on vector going from location towards poi
    rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location)
    # Add homog cam pose based on location an rotation
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
    bproc.camera.add_camera_pose(cam2world_matrix)
```

We sample here five random camera poses, where the location is on a sphere with a radius of 2 around the object. 
Each cameras rotation is such that it looks directly at the object and the camera faces upwards in Z direction.
