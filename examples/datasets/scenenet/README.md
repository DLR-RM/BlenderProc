# SceneNet 

<p align="center">
<img src="../../../images/scenenet_rendering.jpg" alt="Front readme image" width=300>
</p>

The focus of this example is the `loader.SceneNetLoader`, which can be used to load objects from the SceneNet dataset.

We provide a script to download the `.obj` files, see the [scripts](../../scripts/) folder, the texture files can be downloaded [here](https://drive.google.com/file/d/0B_CLZMBI0zcuQ3ZMVnp1RUkyOFk/view?usp=sharing&resourcekey=0-w8JN2r3WQ48eZltxQ-fSwA).

Both are needed to use this dataset properly.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/datasets/scenenet/main.py<PATH_TO_SCENE_NET_OBJ_FILE> <PATH_TO_TEXTURE_FOLDER> examples/datasets/scenenet/output
``` 

* `examples/datasets/scenenet/main.py: path to the python file with pipeline configuration.
* `<PATH_TO_SCENE_NET_OBJ_FILE>`: path to the used scene net `.obj` file, download via this [script](../../scripts/download_scenenet.py)
* `<PATH_TO_TEXTURE_FOLDER>`: path to the downloaded texture files, you can find them [here](http://tinyurl.com/zpc9ppb)
* `examples/datasets/scenenet/output`: path to the output directory.

Please remove the `1Office/3_hereisfree_not_labelled.obj` at it is not supported here, as the scene is in millimeters, and the objects are not correctly placed.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
blenderproc vis hdf5 examples/datasets/scenenet/output/*.hdf5
``` 

## Steps

* The `SceneNetLoader` loads all the objects, which are stored in this one `.obj` file. 
* Each object gets randomly assigned textures based on its name. Therefore, in each run the objects, will have different textures.
 
## Python file (main.py)

### SceneNetLoader 

```python
# Load the scenenet room and label its objects with category ids based on the nyu mapping
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
objs = bproc.loader.load_scenenet(args.scene_net_obj_path, args.scene_texture_path, label_mapping)
```

This loads the SceneNet data object, specified via the `scene_net_obj_path`. 
All objects included in this `.obj` file get a randomly selected texture from the `scene_texture_path` folder.
The `category_id` of each object are set based on their name, check the [table](../../resources/id_mappings/nyu_idset.csv) for more information on the labels.
Be aware if the `unknown_texture_folder` value is not set, that the unknown folder will be assumed to be inside of the `texture_folder` with the name `unknown`.
This folder does *not* exist after downloading the texture files, it has to be manually generated. 
By selecting random texture and putting them in this `unknown_texture_folder`, which can be used on unknown structures.

### SurfaceLighting

```python
# Make all lamp objects emit light
lamps = bproc.filter.by_attr(objs, "name", ".*[l|L]amp.*", regex=True)
bproc.lighting.light_surface(lamps, emission_strength=15)
```

The first function call will make the lamps in the scene emit light, while using the assigned material textures. 

```python
# Also let all ceiling objects emit a bit of light, so the whole room gets more bright
ceilings = bproc.filter.by_attr(objs, "name", ".*[c|C]eiling.*", regex=True)
bproc.lighting.light_surface(ceilings, emission_strength=2)
```

The second function call will make the ceiling emit light and remove any materials placed on it.
This can be changed if desired for more information check out the documentation of `bproc.light_surface()`.

### CameraSampler

```python
# Find all floors in the scene, so we can sample locations above them
floors = bproc.filter.by_cp(objs, "category_id", label_mapping.id_from_label("floor"))
poses = 0
tries = 0
while tries < 10000 and poses < 5:
    tries += 1
    # Sample point above the floor in height of [1.5m, 1.8m]
    location = bproc.sampler.upper_region(floors, min_height=1.5, max_height=1.8)
    # Check that there is no object between the sampled point and the floor
    _, _, _, _, hit_object, _ = bproc.object.scene_ray_cast(location, [0, 0, -1])
    if hit_object not in floors:
        continue

    # Sample rotation (fix around X and Y axis)
    rotation = np.random.uniform([1.2217, 0, 0], [1.2217, 0, 2 * np.pi])
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation)

    # Check that there is no obstacle in front of the camera closer than 1m
    if not bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0}, bvh_tree):
        continue

    # Check that the interesting score is not too low
    if bproc.camera.scene_coverage_score(cam2world_matrix) < 0.1:
        continue

    # If all checks were passed, add the camera pose
    bproc.camera.add_camera_pose(cam2world_matrix)
    poses += 1
```

We sample here five random camera poses, where the location is above the object floor.
So all cameras will be sampled above the floor, with a certain height.
In the end, we perform a check that the sampled pose is directly above a floor and not an object.
Furthermore, we use a `bproc_camera_scene_coverage_score()` here, which tries to increase the amount of objects in a scene. 
All of these steps ensure that the cameras are spread through the scene and are focusing on many objects.

Be aware that it might be possible, if the values are to high, that the CameraSampler will try for a very long time new poses to fulfill the given conditions.
Best is always to check with low values and then increasing them until they don't work anymore.
