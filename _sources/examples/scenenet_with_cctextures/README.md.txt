# SceneNet with CCTextures

<p align="center">
<img src="rendering.jpg" alt="Front readme image" width=300>
</p>

The focus of this example is to show the correct usage of the MaterialRandomizer in a more complex context.

We provide a script to download the `.obj` files, see the [scripts](../../scripts/) folder, the texture files can be downloaded [here](http://tinyurl.com/zpc9ppb).

It is also necessary to download the textures from cc_textures we provide a script [here](../../scripts/download_cc_textures.py).

All three are needed to use this example properly.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/scenenet_with_cctextures/config.yaml <PATH_TO_SCENE_NET_OBJ_FILE> <PATH_TO_TEXTURE_FOLDER> resources/cctextures examples/scenenet_with_cctextures/output
``` 

* `examples/scenenet_with_cctextures/config.yaml`: path to the configuration file with pipeline configuration.
* `<PATH_TO_SCENE_NET_OBJ_FILE>`: path to the used scene net `.obj` file, download via this [script](../../scripts/download_scenenet_with_cctextures.py)
* `<PATH_TO_TEXTURE_FOLDER>`: path to the downloaded texture files, you can find them [here](http://tinyurl.com/zpc9ppb)
* `resources/cctextures`:  path to the cctexture folder, downloaded via the script.
* `examples/scenenet_with_cctextures/output`: path to the output directory.


## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
python scripts/visHdf5Files.py examples/scenenet_with_cctextures/output/*.hdf5
``` 

## Steps

* The `SceneNetLoader` loads all the objects, which are stored in this one `.obj` file. 
* Each object gets randomly assigned textures based on its name. Therefore, in each run the objects, will have different textures.
 
## Config file

### Global

```yaml
{
    "module": "main.Initializer",
    "config": {
      "global": {
        "output_dir": "<args:2>",
        "max_bounces": 200,
        "diffuse_bounces": 200,
        "glossy_bounces": 200,
        "transmission_bounces": 200,
        "transparency_bounces": 200
      }
    }
}
```

We define here besides the usual `output_dir` also the amount of light bounces done by the path tracer.
Usually these values can be quite low, but if the materials are more complex higher bounce numbers give better results.
However, they increase the render time slightly and that's why they are usually turned off.

### SceneNetLoader 

```yaml
{
    "module": "loader.SceneNetLoader",
    "config": {
      "file_path": "<args:0>",
      "texture_folder": "<args:1>"
    }
}
```

This module loads the SceneNet data object, specified via the `file_path`. 
All objects included in this `.obj` file get a randomly selected texture from the `texture_folder`.
The `category_id` of each object are set based on their name, check the [table](../../resources/id_mappings/nyu_idset.csv) for more information on the labels.

### CameraSampler

```yaml
{
    "module": "camera.CameraSampler",
    "config": {
      "cam_poses": [{
        "number_of_samples": 5, # amount of camera samples
        "proximity_checks": {
          "min": 1.0
        },
        "location": {
          "provider": "sampler.UpperRegionSampler",
          "min_height": 1.5,
          "max_height": 1.8,
          "to_sample_on": {
            "provider": "getter.Entity",
            "conditions": {
              "cp_category_id": 2  # 2 stands for floor
            }
          }
        },
        "rotation": {
          "value": {
            "provider":"sampler.Uniform3d",
            "max":[1.2217, 0, 6.283185307],
            "min":[1.2217, 0, 0]
          }
        },
        "check_if_pose_above_object_list": {
          "provider": "getter.Entity",
          "conditions": {
            "cp_category_id": 2,
            "type": "MESH"
          }
        }
      }]
    }
}
```

We sample here five random camera poses, where the location is above the object with the `category_id: 2`, which is the floor.
So all cameras will be sampled above the floor, with a certain height.
In the end, we perform a check with `check_if_pose_above_object_lis` that the sampled pose is directly above a floor and not an object.

### CCMaterialLoader

```yaml
{
  "module": "loader.CCMaterialLoader",
  # you can use the scripts/download_cc_textures.py to download them
  "config": {
    "folder_path": "<args:2>",
    "preload": True
  }
}
```

This module loads empty materials, corresponding to the materials ,which are available at [cc0textures.com](https://cc0textures.com/).
It assumes the textures have been downloaded via the [script](../../scripts/download_cc_textures.py). 

As the loading of all the images is quite time consuming, we preload here only the structure, but not the actual images.
Each material will have a custom property `"is_cc_texture": True`.

This module only sets up the materials which can then be used by other modules.

### MaterialRandomizer 

```yaml
    {
      "module": "manipulators.EntityManipulator",
      "config": {
        "selector": {
          "provider": "getter.Entity",
          "conditions": {
            "type": "MESH"
          }
        },
        "cf_randomize_materials": {
          "randomization_level": 0.4,
          "materials_to_replace_with": {
            "provider": "getter.Material",
            "random_samples": 1,
            "conditions": {
              "cp_is_cc_texture": True  # this will return one random loaded cc textures
            }
          }
        }
      }
    }
```

This builds up on the [material_randomizer](../material_randomizer/README.md) example.

We also use the `randomization_level` and set it `0.4`.

Furthermore, we select all the materials, we want to use for the replacing, as there are only SceneNet objects loaded, we do not specify, which objects materials we want to replace.
Each material loaded by CCMaterialLoader set the `cp_is_cc_texture` custom property to true.

### CCMaterialLoader

```yaml
{
  "module": "loader.CCMaterialLoader",
  # you can use the scripts/download_cc_textures.py to download them
  "config": {
    "folder_path": "<args:2>",
    "fill_used_empty_materials": True
  }
}
```

Now the empty materials, which have been used by the `manipulators.EntityManipulator` are filled with the actual images.
If this is not done, all the materials will be empty.

### SceneNetLighting

```yaml
{
    "module": "lighting.SurfaceLighting",
    "config": {
      "selector": {
        "provider": "getter.Entity",
          "conditions": {
            "name": ".*lamp.*"
          }
      },
      "emission_strength": 15.0,
      "keep_using_base_color": True
    }
}
```

The first module call will make the lamps in the scene emit light, while using the assigned material textures.

```yaml
{
    "module": "lighting.SurfaceLighting",
    "config": {
      "selector": {
        "provider": "getter.Entity",
        "conditions": {
          "name": "Ceiling"
        },
        "emission_strength": 2.0
      }
    }
}
```

The second module call will make the ceiling emit light and remove any materials placed on it.
This can be changed if desired for more information check out the documentation of the module.
