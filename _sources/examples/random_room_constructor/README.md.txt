# Random Room Constructor

<p align="center">
<img src="rendered_example.jpg" alt="Front readme image" width=400>
</p>

This example explains the `RandomRoomConstructor`. This module can build random rooms and place objects loaded from other modules inside of it.

This current example uses the `CCMaterialLoader`. So download the textures from cc_textures we provide a script [here](../../scripts/download_cc_textures.py).
It also uses the `IkeaLoader`, for that please see the [ikea example](../ikea/README.md). 

Both are needed to use to this example.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/random_room_constructor/config.yaml resources/ikea resources/cctextures examples/random_room_constructor/output
``` 

* `<PATH_TO_IKEA>`: path to the downloaded IKEA dataset, see the [scripts folder](../../scripts) for the download script. 
* `resources/cctextures`: path to CCTextures folder, see the [scripts folder](../../scripts) for the download script.
* `examples/random_room_constructor/output`: path of the output directory.

Make sure that you have downloaded the `ikea` dataset and the `cctextures` before executing.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
python scripts/visHdf5Files.py examples/random_room_constructor/output/*.hdf5
``` 

## Steps

* At first the `CCMaterialLoader` is used to load the `cctextures`, these can then be used in the `RandomRoomConstructor`.
* Then the `RandomRoomConstructor` is called:
  * It first builds up a floor plan, based on the given parameters, for a detailed explanation of the keys see the documentation.
  * After that the walls, ceiling and floor are colored with materials from the `CCMaterialLoader`.  
  * Then the `IkeaLoader` module is called 15 times, to load a variety of different objects, which are then placed collision free in the room.
 
## Config file

### CCMaterialLoader 

```yaml
{
  "module": "loader.CCMaterialLoader",
  "config": {
    "used_assets": ["Bricks", "Wood", "Carpet", "Tile", "Marble"]
  }
}
```

This module loads the `cctextures` downloaded via the script, here only the assets which have one of the names of the list in their name are used.
This makes it more realistic as things like `"Asphalt"` are not commonly found inside.

### RandomRoomConstructor 

```yaml
{
  "module": "constructor.RandomRoomConstructor",
  "config": {
    "floor_area": 25,
    "amount_of_extrusions": 5,
    "used_loader_config": [
      {
        "module": "loader.IKEALoader",
        "config": {
          "category": ["bed", "chair", "desk", "bookshelf"]
        },
        "amount_of_repetitions": 15
      },
    ]
  }
}
```

The `RandomRoomConstructor` constructs a random floor plane and builds the corresponding wall and ceiling.
The room will have a floor area of 25 square meters, and it will have at most 5 extrusions. 
An extrusion is a corridor, which stretches away from the basic rectangle in the middle. 
These can be wider or smaller, but never smaller than the minimum `corridor_width`.
The module will automatically split the 25 square meter over all extrusions.

After creating the floor plan and the walls, it will repeat the `IKEALoader` for 15 times, these loaded objects must belong to the four defined categories.
These objects are than randomly placed inside the room. 

### SurfaceLighting

```yaml
{
    "module": "lighting.SurfaceLighting",
    "config": {
      "selector": {
        "provider": "getter.Entity",
        "conditions": {
          "name": "Ceiling"
        },
        "emission_strength": 4.0
      }
    }
}
```

This module will make the ceiling emit light and remove any materials placed on it. 
This can be changed if desired for more information check out the documentation of the module.

### CameraSampler

```yaml
{
    "module": "camera.CameraSampler",
    "config": {
      "cam_poses": [{
        "number_of_samples": 5,
        "proximity_checks": {
          "min": 1.2
        },
        "location": {
          "provider": "sampler.UpperRegionSampler",
          "min_height": 1.5,
          "max_height": 1.8,
          "to_sample_on": {
            "provider": "getter.Entity",
            "index": 0,
            "conditions": {
              "name": "Floor",
              "type": "MESH"
            }
          }
        },
        "rotation": {
          "value": {
            "provider":"sampler.Uniform3d",
            "max":[1.4217, 0, 6.283185307],
            "min":[1.0, 0, 0]
          }
        },
        "min_interest_score": 0.4,
        "check_if_pose_above_object_list": {
          "provider": "getter.Entity",
          "conditions": {
            "name": "Floor",
            "type": "MESH"
          }
        }
      }]
    }
}
```

We sample here five random camera poses, where the location is above the object with the `name: "Floor"`, which was constructed by the `RandomRoomConstructor`.
So all cameras will be sampled above the floor, with a certain height.
In the end, we perform a check with `check_if_pose_above_object_list` that the sampled pose is directly above a floor and not an object.
Furthermore, we use a `min_interest_score` here, which tries to increase the amount of objects in a scene. 
All of these steps ensure that the cameras are spread through the scene and are focusing on many objects.

Be aware that it might be possible, if the values are too high, that the CameraSampler will try for a very long time new poses to fulfill the given conditions.
Best is always to check with low values and then increase them until they don't work anymore.
