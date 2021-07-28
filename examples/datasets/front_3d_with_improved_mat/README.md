# 3D Front Dataset with improved mat 

<p align="center">
<img src="rendering_0.png" alt="Front readme image" width=375>
<img src="rendering_1.png" alt="Front readme image" width=375>
</p>

In this example we explain to you how to use the 3D-Front Dataset with the BlenderProc pipeline in combination with the CCMaterialLoader.
This is an advanced example, make sure that you have executed the basic examples before proceeding to this one, especially the `front_3d` example.
It is also necessary to download the textures from cc_textures, we provide a script [here](../../scripts/download_cc_textures.py).

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/datasets/front_3d_with_improved_mat/config.yaml {PATH_TO_3D-Front-Json-File} {PATH_TO_3D-Future} {PATH_TO_3D-Front-texture} resources/cctextures examples/datasets/front_3d_with_improved_mat/output  
```

* `examples/datasets/front_3d_with_improved_mat/config.yaml`: path to the configuration file with pipeline configuration.

The three arguments afterwards are used to fill placeholders like `<args:0>` inside this config file.
* `PATH_TO_3D-Front-Json-File`: path to the 3D-Front json file 
* `PATH_TO_3D-Future`: path to the folder where all 3D-Future objects are stored 
* `PATH_TO_3D-Front-texture`: path to the folder where all 3D-Front textures are stored 
* `resources/cctextures`: path to the cc texture folder
* `examples/datasets/front_3d_with_improved_mat/output`: path to the output directory

Be aware that the default path for the CCMaterialLoader is used, if you want to change this please refer to the documentation in the `CCMaterialLoader` class.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/datasets/front_3d_with_improved_mat/output/0.hdf5
```

## Steps

* Loads the `.json` file: `loader.Front3DLoader` module. It loads all modules and creates the rooms, it furthermore also adds emission shaders to the ceiling and lamps.
* Sets the category_id of the background to 0: `manipulators.WorldManipulator`
* Adds cameras to the scene: `camera.Front3DCameraSampler`
* Loads the cc Materials: `loader.CCMaterialLoader` 
* Several material Randomizers are used to replace the floor, baseboards and walls materials with cc materials: `manupulators.EntityManipulator`
* Renders rgb, normals: `renderer.RgbRenderer` module.
* Renders semantic segmentation: `renderer.SegMapRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module, removes unnecessary channels for the `"distance"`

## Config file

#### CCMaterialLoader

```yaml
{
  "module": "loader.CCMaterialLoader",
  "config": {
    "folder_path": "<args:2>",
    "used_assets": ["Bricks", "Wood", "Carpet", "Tile", "Marble"]
  }
}
```

The `folder_path` if the script was used, should be `"resources/cctextures"`
This module loads the assets which names contain a string listed in `"used_assets"`.
These will be later used to replace the materials in the 3D-Front scenes.

#### Entity Manipulator

```yaml
    {
      "module": "manipulators.EntityManipulator",
      "config": {
        "selector": {
          "provider": "getter.Entity",
          "conditions": {
            "name": "Floor.*"
          }
        },
        "cf_randomize_materials": {
          "randomization_level": 0.95,
          "materials_to_replace_with": {
            "provider": "getter.Material",
            "random_samples": 1,
            "conditions": {
              "cp_is_cc_texture": True
            }
          }
        }
      }
    }
```

This is one of the `manipulators.EntityManipulator` which swaps the materials of the selected objects, with the materials which are used to replace them.
It will replace 95% of all materials of object, which are selected via the `getter.Entity`. 
The materials which are used to replace the existing ones all have to be from the CCMaterialLoader, which adds to each loaded material the custom property of `"cp_is_cc_texture"`.

A further example is: 

```yaml
    {
      "module": "manipulators.EntityManipulator",
      "config": {
        "selector": {
          "provider": "getter.Entity",
          "conditions": {
            "name": "Wall.*"
          }
        },
        "cf_randomize_materials": {
          "randomization_level": 0.1,
          "materials_to_replace_with": {
            "provider": "getter.Material",
            "random_samples": 1,
            "conditions": {
              "cp_is_cc_texture": True,
              "cp_asset_name": "Marble.*"
            }
          }
        }
      }
    }
```

Here the materials of all walls are replaced, but instead of using all loaded materials only the cc materials, which names start with `"Marble"`.
Also pay attention that only 10% of all materials are replaced, to not over load the rooms with marble.
