# ShapeNet with Scenenet

<p align="center">
<img src="../../../images/shapenet_with_scenenet_rendering.jpg" alt="Front readme image" width=550>
</p>

The focus of this example is the `loader.ShapeNetLoader` in combination with the SceneNet loader, this is an advanced example, please make sure that you have read:

* [shapenet](../shapenet/README.md): Rendering ShapeNet objects 
* [scenenet](../scenenet/README.md): Rendering SceneNet scenes with sampled camera poses.


## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/datasets/shapenet_with_scenenet/main.py <PATH_TO_SCENE_NET_OBJ_FILE> <PATH_TO_TEXTURE_FOLDER> <PATH_TO_ShapeNetCore.v2> examples/datasets/shapenet_with_scenenet/output
``` 

* `examples/datasets/shapenet_with_scenenet/main.py`: path to the python file with pipeline configuration.
* `<PATH_TO_SCENE_NET_OBJ_FILE>`: path to the used SceneNet `.obj` file, download via this [script](../../scripts/download_scenenet.py)
* `<PATH_TO_TEXTURE_FOLDER>`: path to the downloaded texture files, you can find them [here](http://tinyurl.com/zpc9ppb)
* `<PATH_TO_ShapeNetCore.v2>`: path to the downloaded shape net core v2 dataset, get it [here](http://www.shapenet.org/) 
* `examples/datasets/shapenet_with_scenenet/output`: path to the output directory.

As this example requires a bed to be present in the scene, it will only work with the `1Bedroom/*` SceneNet scenes.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
blenderproc vis hdf5 examples/datasets/shapenet_with_scenenet/output/*.hdf5
``` 

## Steps

* At first the SceneNet scene is loaded and we add the custom property `cp_physics` to make sure that the sampled ShapeNet objects, bounds of the SceneNet scene.
* As explained in the [scenenet](../scenenet/README.md) example, the textures are randomly sampled.
* The ShapeNetLoader loads all the object paths with the `synset_id` = `02801938`, this id stands for the category `basket`.
* One of them is now randomly selected and loaded.
* Then we select that one object and change its location to be above an object with the `catgory_id = 4`, which stands for bed.
* We also add a solidify modifier as a few of the objects in the ShapeNet dataset have only a really thin outer shell, this might lead to bad results in the physics simulation.
* The physics simulation is run to let the ShapeNet object fall down on the bed.
* We finally sample some cameras around this ShapeNet object, which are located in a HalfSphere above the ShapeNet object.
* Now we only have to render it and store the results it in a `.hdf5` container


## Python file (main.py)

### SceneNetLoader

```python
# Load the scenenet room and label its objects with category ids based on the nyu mapping
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
room_objs = bproc.loader.load_scenenet(args.scene_net_obj_path, args.scene_texture_path, label_mapping)
```

This loader automatically loads a SceneNet scene/house given the corresponding `.obj` file. 
The textures are randomly sampled from the texture folder, for more information see the [scenenet](../scenenet/README.md) example.
The `bproc.loader.load_scenenet()` also sets the `category_id` of each object, such that semantic segmentation maps can be rendered in a following step.


### ShapeNetLoader 

```python
shapenet_obj = bproc.loader.load_shapenet(args.shapenet_path, used_synset_id="02801938")
```


This loads a ShapeNet Object, it only needs the path to the `ShapeNetCore.v2` folder, which is saved in `data_path`.
The `used_synset_id` = `02801938` is set to the id of a basket, which means a random basket will be loaded.

The position will be in the center of the scene and the object will fall during the physics simulation.

### EntityManipulator
 
```python
# Collect all beds
beds = bproc.filter.by_cp(room_objs, "category_id", label_mapping.id_from_label("bed"))
# Sample the location of the ShapeNet object above a random bed
shapenet_obj.set_location(bproc.sampler.upper_region(beds, min_height=0.3, use_ray_trace_check=True))

# Make sure the ShapeNet object has a minimum thickness (this will increase the stability of the simulator)
shapenet_obj.add_modifier("SOLIDIFY", thickness=0.0025)
# Make the ShapeNet object actively participating in the simulation and increase its mass to stabilize the simulation
shapenet_obj.enable_rigidbody(True, mass_factor=2000, collision_margin=0.00001, collision_shape="MESH")
```

With this we change the location and the custom properties of the ShapeNet Object.
For that we first select the object, via the `"filter"`, based on these conditions it returns the ShapeNetObject, which we will manipulate next.

We first set the location to be sampled above an entity, which has the category "bed".
We add a solidify modifier and add mass to get a correct physics interaction.


### PhysicsPositioning

```python
bproc.object.simulate_physics_and_fix_final_poses(
    solver_iters=30,
    substeps_per_frame=40,
    min_simulation_time=0.5,
    max_simulation_time=4,
    check_object_interval=0.25
)
```

We then run the physics simulation, for more information about that please see the [example/physiscs_positioning](../physics_positioning/README.md).
The high mass factor and the small collision margin guarantee that the object does not move too much.
Important here are the amount of `solver_iters` and `substeps_per_frame` as they have to be high, as lot of objects in the ShapeNet dataset consist out of thin small pieces.
Without this they might slide into the SceneNet objects.
