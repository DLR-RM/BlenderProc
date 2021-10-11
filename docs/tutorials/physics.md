# Physics simulation

For e.g. positioning objects randomly on given surface, BlenderProc offers to use blenders rigid body simulator.
In short, using that simulator, objects are dropped on a surface and then fixed to the position where they come to rest.

## Rigidy body components

For an object to take part in the simulation, its rigid body component needs to be enabled via the function `obj.enable_rigidbody()`.
With that function, all physical properties (like mass, friction etc.) can be specified.

### The `active` parameter

The `active` parameter determines whether the object should be actively participate in the simulation (`=True`), i.e. moving around, or acting as an obstacle (`=False`)

### The `collision_shape` parameter

Choosing the `collision_shape` is crucial to achieve a stable simulation.
If your object is convex or you don't mind if it's collision shape is its convex hull, then you should go with the default value which is `CONVEX_HULL`.
This will lead to a fast and stable simulation.

However, if you have non-convex objects and you want to achieve accurate results, using `CONVEX_HULL` might not be an option.
You could use `MESH` instead, however, especially if the object has thin parts, this will make the simulation very instable and your objects might glitch through each other.

#### Convex decomposition

Therefore, in such situations, it is recommended to perform a convex decomposition of your object. 
To do so BlenderProc offers using V-HACD for that:
```python
obj.enable_rigidbody(active=True, collision_shape="COMPOUND")
obj.build_convex_decomposition_collision_shape("<Path where to store vhacd>")
```

First, enable the rigid body element of your object and make its collision shape `COMPOUND`. 
Which means that its collision shape will be the union of the collision shapes of its child objects (=convex parts).

The second command will perform the convex decomposition of the object and set its convex parts as child objects to the original object.
These child objects will not be visible in the rendering, they are only used as collision shapes!
As the convex decomposition takes a few seconds per object, its result is cached and is automatically reused when the decomposition is performed a second time on the same object.

## Run the simulation

### Simulate and fix poses afterwards

In the usual use-case the following command can be used:

```python
bproc.object.simulate_physics_and_fix_final_poses(
    min_simulation_time=4,
    max_simulation_time=20,
    check_object_interval=1
)
```

This will run the simulation and afterwards fix the final resting pose of each object (The simulation itself will be discarded).
When running the physics simulation the module checks in intervals of 1 second, if there are still objects moving. If this is not the case, the simulation is stopped.
Nevertheless, the simulation is run at least for 4 seconds and at most for 20 seconds.

### Just simulate

If you want to render the simulation itself, use the following command

```python
bproc.object.simulate_physics(
    min_simulation_time=4,
    max_simulation_time=20,
    check_object_interval=1
)
```

This will work similar like `bproc.object.simulate_physics_and_fix_final_poses`, however, the whole simulation is kept.
So, if you render your scene afterwards, it will display the simulation itself.

You might need to increase the rendering interval manually:
```python
# This will make the renderer render the first 100 frames of the simulation
bproc.utility.set_keyframe_render_interval(frame_end=100)
```

