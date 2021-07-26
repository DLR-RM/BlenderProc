# SUNCG scene with object switching

![](result.png)

The ObjectReplacer tries to replace objects with other objects.
First, you can specify the group of objects, which should be replaced: `objects_to_be_replaced` 
and second you can select the objects you want to them to replace them with: `objects_to_replace_with`.
Both groups of objects can be selected with the `getter.Entity`

## Usage

Execute in the Blender-Proc main directory:

```
python run.py examples/datasets/suncg_with_object_replacer/config.yaml <path to house.json> <path to new objects> examples/datasets/suncg_with_object_replacer/output
```

* `examples/datasets/suncg_with_object_replacer/config.yaml`: path to the configuration file with pipeline configuration.
* `<path to house.json>`: path to the house.json file of the SUNCG scene you want to render.
* `<path to new objects>`: path to the `objects_to_replace_with`.
* `examples/datasets/suncg_with_object_replacer/output`: path to the output directory.


## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py example/suncg_with_object_replacer/output/0.hdf5
```

## Steps

* Loads a SUNCG scene: `loader.SuncgLoader` module
* Loads new objects: `loader.ObjectLoader` module
* Hides the new loaded objects from the renderer: `manipulators.EntityManipulator` module
* Switch objects in the `objects_to_be_replaced` config with object in `objects_to_replace_with` config: `object.ObjectReplacer` module
* Sample camera positions inside every room: `camera.SuncgCameraSampler` module.
* Automatically adds light sources inside each room: `lighting.SuncgLighting` module.
* Writes sampled camera poses to file: `writer.CameraStateWriter` module.
* Renders rgb, distance and normals: `renderer.RgbRenderer` module.
* Merges all into an `.hdf5` file: `writer.Hdf5Writer` module.

## Config file

### ObjectReplacer

```yaml
    {
      "module": "object.ObjectReplacer",
      "config": {
        "replace_ratio": 1,
        "copy_properties": True,
        "objects_to_be_replaced": {
            "provider": "getter.Entity",
            "conditions": {
              "type": "MESH",
              "cp_coarse_grained_class": "chair"
            }
        },
        "objects_to_replace_with": {
            "provider": "getter.Entity",
            "conditions": {
              "cp_replace": "chair",
              "type": "MESH"
            }
        },
        "ignore_collision_with": {
        "provider": "getter.Entity",
          "conditions": {
            "name": "Floor",
            "type": "MESH"
          }
        },
      }
    }
```

* This module replaces objects from `objects_to_be_replaced` with objects from `objects_to_replace_with`. The module uses for that the `getter.Entity` provider.
* Furthermore, a probability of `switch_probability` can be set to make the switching probabilistic, if no collision happens between `objects_to_replace_with` and objects in the scene.
* When `copy_properties` is set to `True`, the `objects_to_replace_with` gets all the custom properties that the `objects_to_be_replaced` used to have.
* This module doesn't do collision checking between `objects_to_replace_with` and object provided by the `getter.Entity` `ignore_collision_with`.
