# Haven 
<p align="center">
<img src="../../../images/haven_rendered_example.jpg" alt="normals and color rendering of example table" width=300>
</p>

The focus of this example is the [haven dataset](https://3dmodelhaven.com/) collection.

In order to use this example first download all the haven assets via the haven download script:

```shell
blenderproc download haven
```

This will download all 3D models, all environment HDRs and also all textures they provide.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/datasets/haven/main.py resources/haven/models/ArmChair_01/ArmChair_01_2k.blend resources/haven examples/datasets/haven/output
``` 

* `examples/datasets/haven/main.py`: path to the python file with pipeline configuration.
* `resources/haven/models/ArmChair_01/ArmChair_01.blend`:  Path to the blend file, from the haven dataset, browse the model folder, for all possible options
* `resources/haven`: The folder where the `hdri` folder can be found, to load an world environment
* `examples/datasets/haven/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
blenderproc vis hdf5 examples/datasets/haven/output/*.hdf5
``` 

## Steps

* The BlendLoader loads the given blend file and extracts the object
* Then the `HavenEnvironmentLoader` loads a randomly selected HDR image as world environment
 
## Python file (main.py)

### BlendLoader 

```python
# Load the object into the scene
objs = bproc.loader.load_blend(args.blend_path)
```

The `bproc.loader.load_blend()` loads the given blend file and extracts the object from it.

### HavenEnvironmentLoader 

```python
# Set a random hdri from the given haven directory as background
haven_hdri_path = bproc.loader.get_random_world_background_hdr_img_path_from_haven(args.haven_path)
bproc.world.set_world_background_hdr_img(haven_hdri_path)
```

This loader will load a random HDR image and will use it as an environment background for the scene.
