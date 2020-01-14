# BlenderProc
A procedural blender pipeline to generate images for deep learning

The corresponding arxiv paper: https://arxiv.org/abs/1911.01911

## General

In general, one run of the pipeline first loads or constructs a 3D scene, then sets some camera positions inside this scene and in the end renders different types of image (rgb, depth, normals etc.) for each of them.
The blender pipeline consists of different modules, each of them performing one step in the described process.
The modules are selected, ordered and configured via a yaml file.
 
To run the blender pipeline one just has to call the `run.py` script in the main directory together with the desired config file.

```
python run.py config.yaml <additional arguments>
```

This will now run all modules specified in the config file step-by-step in the configured order.

The following modules are already implemented and ready to use:

* Load *.obj files and SunCG scenes
* Automatic lighting of SunCG scenes
* Loading camera positions from file
* Sampling camera positions inside SunCG rooms
* Rendering of rgb, depth, normal and segmentation images
* Merging data into .hdf5 files

For advanced usage which is not covered by these modules, own modules can easily be implemented (see [Writing modules](#writing-modules))

## Examples

* [Basic scene](examples/basic/): A small example loading an .obj file and camera positions before rendering normal and color images.
* [Simple SUNCG scene](examples/suncg_basic/): Loads a suncg scene and camera positions from file before rendering color, normal, segmentation and a depth images.
* [SUNCG scene with camera sampling](examples/suncg_with_cam_sampling/): Loads a suncg scene and automatically samples camera poses in every room before rendering color, normal, segmentation and a depth images.

## Config

A very small config file could look like this:

```yaml
{
  "setup": {
    "blender_install_path": "/home_local/<env:USER>/blender/",
    "blender_version": "blender-2.80-linux-glibc217-x86_64",
    "pip": [
      "h5py"
    ]
  },
  "global": {
    "all": {
      "output_dir": "<args:0>"
    },
    "renderer": {
      "pixel_aspect_x": 1.333333333
    }
  },
  "modules": [
    {
      "name": "renderer.NormalRenderer",
      "config": {
        "samples": 255
      }
    }
  ]
}
```

To prevent the hardcoding of e.q. paths, placeholder are allowed inside the configuration:

 placeholder | replacement
------------ | -------------
`<args:i>` | Is replaced by the ith argument given to the `run.py` script (not including the path of the config file). The numbering starts from zero.
`<env:NAME>` | Is replaced by the value of the environment variable with name `NAME` 


### Setup

When starting the pipeline, the blender version and python packages required for the given config are automatically installed.
Such software related options are specified inside the `setup` section of a config.

property | description
------------ | -------------
`blender_version` | Specifies the exact blender version identifier which should be installed and used for running the pipeline. Look at https://download.blender.org/release/ to find the corresponding identifier to a specific version.
`blender_install_path` | The directory where blender should be installed. Default: `blender/`.
`custom_blender_path` | If you want to use an existing blender installation, you can set this option to the main directory of your blender installation which will then be used for running the blender pipeline. Therefore automatic blender installation is disabled and the options `blender_install_path` and `blender_version` are ignored. 
`pip` | A list of python packages which are required to run the configured pipeline. They are automatically installed inside the blender python environment via `pip install`.


### Modules

The section `modules` consists of a list of dict objects which all specify a module. 
Every of these module specifications has the following properties:

property | description
------------ | -------------
`name` | Specifies the module class to use. Here the name is just its python path starting from inside the `src` directory.
`config` | Contains the module configuration used to customize the action performed by the module.

The modules are executed in the exact same order as they are configured inside the `modules` section.

### Global

This section contains configuration parameters that are relevant for multiple or all modules. 
The configuration specified inside `all` is inherited by all modules, while the config specified inside `<dir>` (e.q. `renderer`) is inherited by all modules with the prefix `<dir>.` (e.q. `renderer.NormalRenderer`)

## Writing modules

A module is a class executing one step in the pipeline.

Here is the basic structure of such a module:

```python
from src.main.Module import Module

class CameraLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)
        [...]

    def run(self):
        [...]
```

The constructor of all modules is called before running any module, also in the order specified in the config file. 
Nevertheless it should only be used for small preparation work, while most of the module\`s work should be done inside `run()`

### Access configuration

The module\`s configuration can be accessed via `self.config`. 
This configuration object has the methods `get_int`, `get_float`, `get_bool`, `get_string`, `get_list`, `get_raw_dict`, each working in the same way.
 * The first parameter specifies the key/name of the parameter to get. By using `/` it is also possible access values nested inside additional dicts (see example below).
 * The second parameter specifies the default value which is returned, if the requested parameter has not been specified inside the config file. If `None` is given, an error is thrown instead.
 
**Example:**


Config file:
```yaml
{
  "global": {
    "all": {
      "output_dir": "/tmp/",
      "auto_tile_size": false
    },
    "renderer": {
      "pixel_aspect_x": 1.333333333
    }
  },
  "modules": [
    {
      "name": "renderer.NormalRenderer",
      "config": {
        "auto_tile_size": true,
        "cycles": {
          "samples": 255
        }
      }
    }
  ]
}
```

Inside the `renderer.NormalRenderer` module:

```python
self.get_int("cycles/samples", 42)  
# -> 255

self.get_float("pixel_aspect_x") 
# -> 1.333333333

self.get_string("output_dir", "output/") 
# -> /tmp/

self.get_bool("auto_tile_size") 
# -> True

self.config.get_int("resolution_x", 512)
# ->  512

self.config.get_int("tile_x") 
# -> throws an error
```

## Undo changes

In some modules it makes sense to revert changes made inside the module to not disturb modules coming afterwards (For example renderer modules should not change the state of the scene).

This often requried funcitonality can be easily done via the `Utility.UndoAfterExecution()` with-statement:

**Example:**
```python
def run(self):
    bpy.context.scene.cycles.samples = 50
    
    with Utility.UndoAfterExecution():
        bpy.context.scene.cycles.samples = 320
        
        print(bpy.context.scene.cycles.samples)
        # Outputs: 320

    print(bpy.context.scene.cycles.samples)
    # Outputs: 50
```

All changes inside the with-block are undone which could also be undone via `CTRL+Z` inside blender.


## Between-module communication

To exchange information between modules the blender's custom properties are used (Blender allows to assign arbitrary information to scenes and objects).
So modules can read out custom properties set by earlier modules and change their behaviour accordingly.

**Example**
* The module `loader.SuncgLoader` adds the custom property `category_id` to every object 
* The module `renderer.SegMapRenderer` reads out this property and sets the segmentation color of every object correspondingly

In this way the `renderer.SegMapRenderer` can also be used without using the `loader.SuncgLoader`. 
The loader used instead just has to also set the `category_id`.
