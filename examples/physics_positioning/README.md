# Physics positioning

![](rendering.png)

This example places some spheres randomly across a bumpy plane without any intersections between objects.
This is done via a physics simulation where the spheres are first placed randomly above the plane and then are influenced by gravity such that they fall down upon the plane until they find a new resting positon.

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py examples/physics_positioning/config.yaml examples/physics_positioning/output
```

Explanation of the arguments:
* `examples/physics_positioning/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/physics_positioning/output`: path to the output directory.

## Steps

* Loads `active.obj` (6 spheres) with `"physics" = ACTIVE`: `loader.ObjectLoader` module.
* Randomly places them: `object.ObjectPoseSampler` module.
* Loads `passive.obj` (one bumpy plane) with `"physics" = PASSIVE`: `loader.ObjectLoader` module.
* Adds a camera and a light: `camera.CameraLoader` and `lighting.LightLoader` module.
* Runs the physics simulation: `object.PhysicsPositioning` module.
* Renders rgb and depth: `renderer.RgbRenderer` module.

## Explanation of the config file

### Load spheres and position them randomly
```yaml
{
  "name": "loader.ObjectLoader",
  "config": {
    "path": "examples/physics_positioning/active.obj",
    "physics": "active"
  }
},
{
  "name": "object.ObjectPoseSampler",
  "config":{
    "pos_sampler":{
      "name":"Uniform3dSampler",
      "parameters":{
        "max":[5, 5, 8],
        "min":[-5, -5, 12]
      }
    },
    "rot_sampler":{
      "name":"Uniform3dSampler",
      "parameters":{
        "max":[0, 0, 0],
        "min":[6.28, 6.28, 6.28]
      }
    }
  }
},
```

First some spheres are loaded from the file `active.obj` and their physics attribute is set to `active`, so that they will later be influenced by gravity. 
Then the `ObjectPoseSampler` is used to place them randomly above the plane.
 
 
### Load plane

```yaml
{
  "name": "loader.ObjectLoader",
  "config": {
    "path": "examples/physics_positioning/passive.obj"
  }
}
```

Now the the plane is loaded from the file `passive.obj`. 
The `physics` attribute will hereby be automatically set to `passive`.
As we load this object after the `ObjectPoseSampler`, the location of the plane is not randomly sampled.

### Run simulation

```yaml
{
  "name": "object.PhysicsPositioning",
  "config": {
    "min_simulation_time": 4,
    "max_simulation_time": 20,
    "check_object_interval": 1
  }
},
```

This module now internally does a physics simulation. 
All objects with `pyhsics` set to `active` will be influenced by gravity, while all `passive` objects will remain steady.
In this way the spheres will fall down until they hit the bumpy plane.

When running the physics simulation the module checks in intervals of 1 second, if there are still objects moving. If this is not the case, the simulation is stopped.
Nevertheless the simulation is run at least for 4 seconds and at most for 20 seconds.

At the end of the simulation the position of all spheres is made fixed again.
In this way we can easily sample random positions of the spheres on top of the bumpy plane.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/suncg_basic/output/0.hdf5
```

## More examples

* [object_pose_sampling](../object_pose_sampling): More on sampling object positions inside simple shapes.