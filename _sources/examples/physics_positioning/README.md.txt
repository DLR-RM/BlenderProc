# Physics positioning

![](rendering.png)

This example places some spheres randomly across a bumpy plane without any intersections between objects.
This is done via a physics simulation where the spheres are first placed randomly above the plane and then are influenced by gravity such that they fall down upon the plane until they find a new resting positon.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/physics_positioning/config.yaml examples/physics_positioning/active.obj examples/physics_positioning/passive.obj examples/physics_positioning/output
```

* `examples/physics_positioning/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/physics_positioning/active.obj`: path to the object file with active objects, i. e. objects which we want to participate in physics simulation.
* `examples/physics_positioning/passive.obj`: path to the object file with passive objects, i. e. objects which we do not want to participate in physics simulation, e.g. plane.
* `examples/physics_positioning/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/physics_positioning/output/0.hdf5
```

## Steps

* Loads `active.obj` (6 spheres) with `"physics" = True`: `loader.ObjectLoader` module.
* Loads `passive.obj` (one bumpy plane) with `"physics" = False`: `loader.ObjectLoader` module.
* Randomly places them: `object.ObjectPoseSampler` module.
* Adds a camera and a light: `camera.CameraLoader` and `lighting.LightLoader` module.
* Runs the physics simulation: `object.PhysicsPositioning` module.
* Renders rgb and distance: `renderer.RgbRenderer` module.

## Config File

### Load active and passive objects

```yaml
{
  "module": "loader.ObjectLoader",
  "config": {
    "path": "<args:0>",
    "add_properties": {
      "cp_physics": True 
      }
  }
}
```
```yaml
{
  "module": "loader.ObjectLoader",
  "config": {
    "path": "<args:1>",
    "add_properties": {
      "cp_physics": False 
    }
  }
}
```

First some spheres are loaded from the file `active.obj` (0th placeholder `<args:0>`) and their physics attribute is set to `True`, so that they will later be influenced by gravity.
Then the plane is loaded from the file `passive.obj` (1th placeholder `<args:1>`). The `physics` attribute will hereby set to `False`. 

### Random positioning

```yaml
{
  "module": "object.ObjectPoseSampler",
  "config": {
    "objects_to_sample": {
      "provider": "getter.Entity",
      "conditions": {
        "cp_physics": True,
        "type": "MESH"
      }
    },
    "pos_sampler": {
      "provider": "sampler.Uniform3d",
      "max": [5, 5, 8],
      "min": [-5, -5, 12]
    },
    "rot_sampler": {
      "provider": "sampler.Uniform3d",
      "max": [0, 0, 0],
      "min": [6.28, 6.28, 6.28]
    }
  }
}
```

The `ObjectPoseSampler` is used to place `active` objects randomly above the plane. `selector` call a Provider `getter.Entity` which allows us to select objects with `True` physics property.
Pose sampling can be done by calling any two appropriate Providers (Samplers). In our case we called `sampler.Uniform3d` twice: once for `pos_sampler` and once for `rot_sampler`.

### Run simulation

```yaml
{
  "module": "object.PhysicsPositioning",
  "config": {
    "min_simulation_time": 4,
    "max_simulation_time": 20,
    "check_object_interval": 1,
    "collision_shape": "MESH"
  }
}
```

This module now internally does a physics simulation. 
All objects with `physics` set to `True` will be influenced by gravity, while all `False` objects will remain steady.
In this way the spheres will fall down until they hit the bumpy plane.
We set the collision shape to `MESH` (default is `CONVEX_HULL`) here to make sure the spheres can drop into the valleys.
Keep in mind that using the mesh collision shape in more complex use-cases can cause performance and glitch issues.

When running the physics simulation the module checks in intervals of 1 second, if there are still objects moving. If this is not the case, the simulation is stopped.
Nevertheless the simulation is run at least for 4 seconds and at most for 20 seconds.

At the end of the simulation the position of all spheres is made fixed again.
In this way we can easily sample random positions of the spheres on top of the bumpy plane.
