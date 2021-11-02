# ShapeNet with SUNCG

<p align="center">
<img src="../../../images/shapenet_with_suncg_rendering.jpg" alt="Front readme image" width=300>
</p>

The focus of this example is the `loader.ShapeNetLoader` in combination with the SUNCG loader, this is an advanced example, please make sure that you have read:


* [shapenet](../shapenet/README.md): Rendering ShapeNet objects 
* [sung_basic](../suncg_basic/README.md): Rendering SUNCG scenes with fixed camera poses.
* [suncg_with_cam_sampling](../suncg_with_cam_sampling/README.md): More on rendering SUNCG scenes with dynamically sampled camera poses.


## Usage

Execute in the BlenderProc main directory:

```
blenderpoc run examples/datasets/shapenet_with_suncg/main.py <PATH_TO_ShapeNetCore.v2> <PATH_TO_SUNCG_HOUSE_JSON> examples/datasets/shapenet_with_suncg/output
``` 

* `examples/datasets/shapenet_with_suncg/main.py`: path to the python file with pipeline configuration.
* `<PATH_TO_ShapeNetCore.v2>`: path to the downloaded shape net core v2 dataset, get it [here](http://www.shapenet.org/) 
* `<PATH_TO_SUNCG_HOUSE_JSON>`: path to a `house.json` file from the SUNCG dataset.
* `examples/datasets/shapenet_with_suncg/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
blenderproc vis hdf5 examples/datasets/shapenet_with_suncg/output/*.hdf5
``` 

## Steps

* At first the SUNCG scene is loaded.
* The ShapeNetLoader loads all the object paths with the `used_synset_id` = `02801938`, this id stands for the category `basket`.
* One of them is now randomly selected and loaded.
* Then we select that one object and change its location to be above an object with the catgory "bed".
* We also add a solidify modifier as a few of the objects in the ShapeNet dataset have only a really thin outer shell, this might lead to bad results in the physics simulation.
* We enable the rigid body component of the objects which makes them participate in physics simulations.
* The physics simulation is run to let the ShapeNet object fall down on the bed.
* We finally sample some cameras around this ShapeNet object, which are located in a HalfSphere above the ShapeNet object.
* Now we only have to render it and store it in a `.hdf5` container


## Python file (main.py)

### SuncgLoader

```python
label_mapping = bproc.utility.LabelIdMapping.from_csv(bproc.utility.resolve_resource(os.path.join('id_mappings', 'nyu_idset.csv')))
suncg_objs = bproc.loader.load_suncg(args.house, label_mapping=label_mapping)
```

This loader automatically loads a SUNCG scene/house given the corresponding `house.json` file. 
Therefore, all objects specified in the given `house.json` file are imported and textured.
The `SuncgLoader` also sets the `category_id` of each object, such that semantic segmentation maps can be rendered in a following step.


### ShapeNetLoader 

```python
# load selected shapenet object
shapenet_obj = bproc.loader.load_shapenet(args.shape_net, used_synset_id="02801938")
```

This loads a ShapeNet Object, it only needs the path to the `ShapeNetCore.v2` folder, which is saved in `data_path`.
The `synset_id` = `02801938` is set to the id of a basket, which means a random basket will be loaded.

The position will be in the center of the scene, and we add the custom property `cp_physics: True` so that the object will fall during the physics simulation.
We also add a custom property to make the selection with `EntityManipulator` in the next step easier.

### EntityManipulator

```python
# Sample a point above any bed
sample_point = bproc.sampler.upper_region(
    objects_to_sample_on=bed_objs,
    min_height=0.75,
    use_ray_trace_check=True
)
# move the shapenet object to the sampled position
shapenet_obj.set_location(sample_point)

# adding a modifier we avoid that the objects falls through other objects during the physics simulation
shapenet_obj.add_modifier(name="SOLIDIFY", thickness=0.001)

# enable rigid body component of the objects which makes them participate in physics simulations
shapenet_obj.enable_rigidbody(active=True, mass_factor=2000, collision_margin=0.0001)
for obj in bproc.filter.all_with_type(suncg_objs, bproc.types.MeshObject):
    obj.enable_rigidbody(active=False, mass_factor=2000, collision_margin=0.0001)
```

With this we change the location of the ShapeNet Object.
For that we first select the object, via the `"filter"`, based on these conditions it returns the ShapeNetObject, which we will manipulate next.

We first set the location to be sampled above an entity, which has the category "bed".
We add a solidify modifier and add mass to get a correct physics interaction.


### PhysicsPositioning

```python
bproc.object.simulate_physics_and_fix_final_poses(min_simulation_time=0.5, max_simulation_time=4, check_object_interval=0.25)
```

We then run the physics simulation, for more information about that please see the [example/physiscs_positioning/README.md](../physics_positioning).
The high mass factor and the small collision margin guarantee that the object does not move too much.
