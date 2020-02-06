# SUNCG scene with object switching

This module tries to switch between `objects_to_be_replaced` objects and `objects_to_replace_with` objects

## Usage

Execute in the Blender-Proc main directory:

```
python run.py examples/suncg_with_object_switcher/config.yaml <path to house.json> examples/suncg_with_object_switcher/output
```

## Steps

* Loads a SUNCG scene
* Switch objects in the `objects_to_be_replaced` config with object in `objects_to_replace_with` config
* Renders color, normal, segmentation and a depth images
* Merges all into an `.hdf5` file

## Explanation of specific parts of the config file


### ObjectReplacer

```yaml
    {
      "module": "manipulators.ObjectReplacer",
      "config": {
        "replace_ratio": 1,
        "copy_properties": True,
        "objects_to_be_replaced": {
            "provider": "getter.Entity",
            "conditions": {
              "coarse_grained_class": "chair"
            }
        },
        "objects_to_replace_with": {
            "provider": "getter.Entity",
            "conditions": {
              "replace": "chair",
              "type": "MESH"
            }
        }
      }
    },
```

* This module tries to switch between `objects_to_be_replaced` objects and `objects_to_replace_with` objects, which the module get using a `getter.Entity`, with probability of `switch_probability` if no collision happens between `objects_to_replace_with` and objects in the scene.
* When `copy_properties` is set to `True`, the `objects_to_replace_with` gets all the custom proprites that the `objects_to_be_replaced` used to have.
