# SUNCG scene with object switching

## Usage

Execute in the Blender-Proc main directory:

```
python run.py examples/suncg_with_object_switcher/config.yaml <path to house.json> examples/suncg_with_object_switcher/output
```

## Steps

* Loads a SUNCG scene
* Loads ikea objects using IkeaObjectLoader
* Switch objects in the scene with loaded ikea objects
* Automatically adds light sources inside each room
* Renders color, normal, segmentation and a depth images
* Merges all into an `.hdf5` file

## Explanation of specific parts of the config file

### IkeaObjectsLoader

```yaml
{
  "name": "loader.IkeaObjectsLoader",
  "config": {
    "mapping": [
      {
        "category": "chair",
        "paths": ["/volume/reconstruction_data/ikea/IKE020017_obj/IKEA-Frosta_Stool-3D.obj", "/volume/reconstruction_data/ikea/IKE160097_obj/IKE160097.obj", "/volume/reconstruction_data/ikea/IKE120005_obj/IKEA-ISALA_coffee_table-3D.obj"]
      },
    ]
  }
},
```

* This module loads all the objets from the `paths` and are given the `category` as a property, and `ikea` property is added and set to 1


### ObjectSwitcher

```yaml
    {
      "name": "manipulators.ObjectSwitcher",
      "config": {
        "switch_probability": 1,
        "selector": {
            "name": "getter.Object",
            "condition": {
              "ikea": 1
            }
        }
      }
    },
```

* This module selects the objects with the property `ikea`
* Replace objects in the scene with the same category as the `ikea` ones with probability of `switch_probability`
