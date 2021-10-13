# Convex decomposition for generating stable and exact collision shapes

![](../../../images/physics_convex_decomposition_rendering.jpg)

When running physical simulations in blender, the choice of the correct collision shapes is crucial to achieve stable results.
While using the `CONVEX_HULL` collision shape results in very stable simulations, the result might look very implausible for non-convex objects (e.q. objects floating).
The `MESH` collision shape allows for more exact collisions, however the simulation also gets very unstable and objects can glitch through each other.

`CONVEX_DECOMPOSITION` is a compromise between both: 
The [V-HACD algorithm](https://github.com/kmammou/v-hacd) is used to decompose a given non-convex object into multiple approximate convex parts.
The union of these parts can then be used as an exact and stable collision shape for the object.

In this example we load a bin and some highly non-convex shapenet objects, apply convex decomposition to generate collision shapes and then let the objects drop into the bin. 

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/physics_convex_decomposition/main.py examples/advanced/physics_convex_decomposition/bin.obj <PATH_TO_ShapeNetCore.v2> examples/advanced/physics_convex_decomposition/output
```

* `examples/advanced/physics_convex_decomposition/main.py`: path to the main python file to run.
* `examples/advanced/physics_convex_decomposition/bin.obj`: path to the object file containing the bin
* `<PATH_TO_ShapeNetCore.v2>`: path to the downloaded shape net core v2 dataset, get it [here](http://www.shapenet.org/)
* `examples/advanced/physics_convex_decomposition/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/advanced/physics_convex_decomposition/output/0.hdf5
```

## Implementation

```python
# Make the bin object passively participate in the physics simulation
bin_obj.enable_rigidbody(active=False, collision_shape="COMPOUND")
# Let its collision shape be a convex decomposition of its original mesh
# This will make the simulation more stable, while still having accurate collision detection
bin_obj.build_convex_decomposition_collision_shape(args.vhacd_path)
```

* The collision shape of the original object is set to `COMPOUND` and will therefore consist of the UNION of their children's collision shapes
* V-HACD is called to do the actual convex decomposition (this may take a while)
* The approximate convex parts are placed as children to the original objects in the scene graph
* The convex parts are hidden during rendering and are provided with `CONVEX_HULL` collision shapes
* The result of the convex decomposition of each object is cached in `resources/decomposition_cache` (key is a hash based on the object's local vertex coordinates). Therefore, running the example a second time will be a lot faster.