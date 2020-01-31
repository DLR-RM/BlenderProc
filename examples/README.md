* [Examples overview](#examples-overview)
* [Config file example](#config-file-example)
* [Writing your own modules](#writing-your-own-modules)

# Examples overview

Each folder contains a different example, some of those need external datasets.

## Basic

When you are feeling brave enough to start with some actual examples, start with a [basic example](basic)!
It will give you an idea about how, why and when certain things happen.

## Debug

To understand what happens during the execution of the pipeline and certain modules it is sometimes useful to use blender directly. 
How to do this check out the folder [debugging](debugging).

## Sampling

All samplers share the same structure, so understanding one of them makes it easier to understand the others as well.
Here are examples for camera, light and object pose sampling: 

* [camera sampling](camera_sampling): Sampling of different camera positions inside of a shape with constraints for the rotation.
* [light sampling](light_sampling): Sampling of light positions, this is the same behavior needed for the object and camera sampling.
* [object pose sampling](object_pose_sampling): Shows a more complex use of a 6D pose sampler.

## Physics

* [physics_positioning](physics_positioning): Overview of an easy to use module we provide for using physics in your simulations.

## Entity manipulation

* [entity manipulation](entity_manipulation): Changing various parameters of entities via selecting them through config file.

## Dataset related examples

We provided limited dataset support, for example for SUNCG, Replica, CoCo Annotations and others.

These can be found in:
* [replica-dataset](replica-dataset)
* [suncg_basic](suncg_basic)
* [suncg_with_cam_sampling](suncg_with_cam_sampling)
* [CoCo annotations](coco_annotations)

# Config file example

A very small config file could look like this:

```yaml
{
  "setup": {
    "blender_install_path": "/home_local/<env:USER>/blender/",
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


## Setup

When starting the pipeline, the blender version and python packages required for the given config are automatically installed.
Such software related options are specified inside the `setup` section of a config.

property | description
------------ | -------------
`blender_install_path` | The directory where blender should be installed. Default: `blender/`.
`custom_blender_path` | If you want to use an existing blender installation, you can set this option to the main directory of your blender installation which will then be used for running the blender pipeline. Therefore automatic blender installation is disabled and the options `blender_install_path` are ignored, we only support blender version 2.81. 
`pip` | A list of python packages which are required to run the configured pipeline. They are automatically installed inside the blender python environment via `pip install`.


## Modules

The section `modules` consists of a list of dict objects which all specify a module. 
Every of these module specifications has the following properties:

property | description
------------ | -------------
`name` | Specifies the module class to use. Here the name is just its python path starting from inside the `src` directory.
`config` | Contains the module configuration used to customize the action performed by the module.

The modules are executed in the exact same order as they are configured inside the `modules` section.

## Global

This section contains configuration parameters that are relevant for multiple or all modules. 
The configuration specified inside `all` is inherited by all modules, while the config specified inside `<dir>` (e.q. `renderer`) is inherited by all modules with the prefix `<dir>.` (e.q. `renderer.NormalRenderer`)

# Writing your own modules

If our modules lack some specific functionality, you always can write your own module.

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

## Access configuration

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

