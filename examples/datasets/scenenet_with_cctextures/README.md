# SceneNet with CCTextures

<p align="center">
<img src="../../../images/scenenet_with_cctextures_rendering.jpg" alt="Front readme image" width=300>
</p>

The focus of this example is to show the correct usage of the MaterialRandomizer in a more complex context.

We provide a script to download the `.obj` files, see the [scripts](../../scripts/) folder, the texture files can be downloaded [here](https://drive.google.com/file/d/0B_CLZMBI0zcuQ3ZMVnp1RUkyOFk/view?usp=sharing&resourcekey=0-w8JN2r3WQ48eZltxQ-fSwA).

It is also necessary to download the textures from cc_textures we provide a script [here](../../scripts/download_cc_textures.py).

All three are needed to use this example properly.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/datasets/scenenet_with_cctextures/main.py <PATH_TO_SCENE_NET_OBJ_FILE> <PATH_TO_TEXTURE_FOLDER> resources/cctextures examples/datasets/scenenet_with_cctextures/output
``` 

* `examples/datasets/scenenet_with_cctextures/main.py`: path to the python file with pipeline configuration.
* `<PATH_TO_SCENE_NET_OBJ_FILE>`: path to the used scene net `.obj` file, download via this [script](../../scripts/download_scenenet_with_cctextures.py)
* `<PATH_TO_TEXTURE_FOLDER>`: path to the downloaded texture files, you can find them [here](http://tinyurl.com/zpc9ppb)
* `resources/cctextures`:  path to the cctexture folder, downloaded via the script.
* `examples/datasets/scenenet_with_cctextures/output`: path to the output directory.


## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
blenderproc vis hdf5 examples/datasets/scenenet_with_cctextures/output/*.hdf5
``` 

## Steps

* The `SceneNetLoader` loads all the objects, which are stored in this one `.obj` file. 
* Each object gets randomly assigned textures based on its name. Therefore, in each run the objects, will have different textures.
 
## Python file (main.py)

Here we focus on the cc material. For every other step please have a look in the scenenet example.

### CCMaterialLoader

```python
# Load all recommended cc materials, however don't load their textures yet
cc_materials = bproc.loader.load_ccmaterials(args.cc_material_path, preload=True)
```

This loads empty materials, corresponding to the materials ,which are available at [cc0textures.com](https://cc0textures.com/).
It assumes the textures have been downloaded via the [script](../../scripts/download_cc_textures.py). 

As the loading of all the images is quite time consuming, we preload here only the structure, but not the actual images.

This only sets up the materials which can then be used by other functions.

### MaterialRandomizer 

```python
# Go through all objects
for obj in objs:
    # For each material of the object
    for i in range(len(obj.get_materials())):
        # In 40% of all cases
        if np.random.uniform(0, 1) <= 0.4:
            # Replace the material with a random one from cc materials
            obj.set_material(i, random.choice(cc_materials))
```

This builds up on the [material_randomizer](../material_randomizer/README.md) example.

The randomization level is set to `0.4`.

Furthermore, we select all the materials, we want to use for the replacing, as there are only SceneNet objects loaded, we do not specify, which objects materials we want to replace.

### CCMaterialLoader

```python
# Now load all textures of the materials that were assigned to at least one object
bproc.loader.load_ccmaterials(args.cc_material_path, fill_used_empty_materials=True)
```

Now the empty materials, which have been used by the `manipulators.EntityManipulator` are filled with the actual images.
If this is not done, all the materials will be empty.
