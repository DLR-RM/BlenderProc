# ShapeNet 

<p align="center">
<img src="rendering.jpg" alt="Front readme image" width=300>
</p>

The focus of this example is the `loader.ShapeNetLoader` in combination with the SUNCG loader, this is an advanced example, please make sure that you have read:


* [shapenet](../shapenet/README.md): Rendering ShapeNet objects 
* [sung_basic](../suncg_basic/README.md): Rendering SUNCG scenes with fixed camera poses.
* [suncg_with_cam_sampling](../suncg_with_cam_sampling/README.md): More on rendering SUNCG scenes with dynamically sampled camera poses.


## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/shapenet_with_suncg/config.yaml <PATH_TO_ShapeNetCore.v2> <PATH_TO_SUNCG_HOUSE_JSON> examples/shapenet_with_suncg/output
``` 

* `examples/shapenet_with_suncg/config.yaml`: path to the configuration file with pipeline configuration.
* `<PATH_TO_ShapeNetCore.v2>`: path to the downloaded shape net core v2 dataset, get it [here](http://www.shapenet.org/) 
* `<PATH_TO_SUNCG_HOUSE_JSON>`: path to a `house.json` file from the SUNCG dataset.
* `examples/shapenet_with_suncg/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
python scripts/visHdf5Files.py examples/shapenet_with_suncg/output/*.hdf5
``` 

## Steps

* At first the SUNCG scene is loaded and we add the custom property `cp_physics` to make sure that the sampled ShapeNet objects, bounds of the SUNCG scene.
* The ShapeNetLoader loads all the object paths with the `synset_id` = `02801938`, this id stands for the category `basket`.
* One of them is now randomly selected and loaded.
* Then we select that one object and change its location to be above an object with the `catgory_id = 1`, which stands for bed.
* We also add a solidify modifier as a few of the objects in the ShapeNet dataset have only a really thin outer shell, this might lead to bad results in the physics simulation.
* The physics simulation is run to let the ShapeNet object fall down on the bed.
* We finally sample some cameras around this ShapeNet object, which are located in a HalfSphere above the ShapeNet object.
* Now we only have to render it and store it in a `.hdf5` container


## Config file

### Global

```yaml
{
  "module": "main.Initializer",
  "config": {
    "global": {
      "output_dir": "<args:2>",
    }
  }
}
```

The same as in the basic example.

### SuncgLoader

```yaml
{
  "module": "loader.SuncgLoader",
  "config": {
    "path": "<args:1>"
    "add_properties": {
      "cp_physics": False
    }
  }
}
```

This loader automatically loads a SUNCG scene/house given the corresponding `house.json` file. 
Therefore, all objects specified in the given `house.json` file are imported and textured.
The `SuncgLoader` also sets the `category_id` of each object, such that semantic segmentation maps can be rendered in a following step.

To each loaded object do we add the custom property `cp_physics: False`, which means that all of the objects behave passively in a physics simulation.

### ShapeNetLoader 

```yaml
{
  "module": "loader.ShapeNetLoader",
  "config": {
    "data_path": "<args:0>",
    "used_synset_id": "02801938",
    "add_properties": {
      "cp_shape_net_object": True
    }
  }
}
```
This module loads a ShapeNet Object, it only needs the path to the `ShapeNetCore.v2` folder, which is saved in `data_path`.
The `synset_id` = `02801938` is set to the id of a basket, which means a random basket will be loaded.

The position will be in the center of the scene, and we add the custom property `cp_physics: True` so that the object will fall during the physics simulation.
We also add a custom property to make the selection with `EntityManipulator` in the next step easier.

### EntityManipulator
 
```yaml
{
    "module": "manipulators.EntityManipulator",
    "config": {
      # get all shape net objects, as we have only loaded one this returns only one entity
      "selector": {
        "provider": "getter.Entity",
        "conditions": {
          "cp_shape_net_object": True,
          "type": "MESH"
        }
      },
      # Sets the location of this entity above a bed
      "location": {
        "provider": "sampler.UpperRegionSampler",
        "min_height": 0.75,
        "to_sample_on": {
            "provider": "getter.Entity",
            "conditions": {
              "cp_category_id": 4, # 4 is the category of the bed
              "type": "MESH"
            }
    
        }
      },
      # by adding a modifier we avoid that the objects falls through other objects during the physics simulation
      "cf_add_modifier": {
        "name": "Solidify",
        "thickness": 0.001
      }
    }
}
```

With the `EntityManipulator` do we change the location and the custom properties of the ShapeNet Object.
For that we first select the object, via the `"selector"`, based on these conditions it returns the ShapeNetObject, which we will manipulate next.

We first set the location to be sampled above a entity, which has the `category_id: 1` (1 stands for bed).
Finally, we add a solidify modifier to get a correct physics interaction.

### PhysicsPositioning

```yaml
{
  "module": "object.PhysicsPositioning",
  "config": {
    "min_simulation_time": 0.5,
    "max_simulation_time": 4,
    "check_object_interval": 0.25,
    "mass_scaling": True,
    "mass_factor": 2000,
    "collision_margin": 0.0001
  }
}
```

We then run the physics simulation, for more information about that please see the [example/physiscs_positioning/README.md](../physics_positioning).
The high mass factor and the small collision margin guarantee that the object does not move too much.

### CameraSampler

```yaml
{
    "module": "camera.CameraSampler",
    "config": {
      "cam_poses": [
      {
        "number_of_samples": 5,
        "location": {
          "provider":"sampler.PartSphere",
          "center": {
            "provider": "getter.POI",
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "cp_shape_net_object": True,
                "type": "MESH"
              }
            }
          },
          "distance_above_center": 0.5,
          "radius": 2,
          "mode": "SURFACE"
        },
        "rotation": {
          "format": "look_at",
          "value": {
            "provider": "getter.POI",
            "selector": {
              "provider": "getter.Entity",
              "conditions": {
                "cp_shape_net_object": True,
                "type": "MESH"
              }
            }
          }
        }
      }
      ]
    }
}
```

We sample here five random camera poses, where the location is on a sphere with a radius of 2 around the ShapeNet object, which we select via a `getter.Entity` provider, which feeds into a `getter.POI`, which returns the bounding box center of the selected object. 
Each cameras rotation is such that it looks directly at the object and the camera faces upwards in Z direction, we use the same selection for the center of the object as for the location.

We render again and store the result inside of `.hdf5` container.
