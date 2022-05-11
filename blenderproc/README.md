# Source code

Each module used in BlenderProc is defined in here. The folders structure the modules according to their use-case.

## Contents

* [Overview](#overview)
* [Writing your own modules](#writing-your-own-modules)

## Overview

As mentioned before, all of the source code relevant to the key features (i.e. modules) of BlenderProc is presented here.
The [main](main) folder contains the Module base class and the Pipeline class, which gets executed by the `blenderproc run` and `blenderproc debug`

Existing modules are placed in use-case-dependent folders:
* [camera](camera): camera loading and camera pose sampling.
* [composite](composite): complex (composite, duh) modules that are using other existing modules.
* [constructor](constructor): constructing scenery and adding objects.
* [lighting](lighting): light source loading, light source pose sampling, dataset-specific light loaders.
* [loader](loader): .obj, .ply, etc. object loading, dataset-specific object loading.
* [manipulators](manipulators): manipulating of the World and different entities present in the scene.
* [materials](materials): manipulating materials.
* [object](object): object pose manipulation, physics between-object interaction, sampling and geometry manipulation.
* [postprocessing](postprocessing): changing the pipeline output inside of a .hdf5 container.
* [provider](provider): samplers and getters used for sampling various values, selecting objects, etc.
* [renderer](renderer): RGB, distance, etc. rendering.
* [utility](utility): an assortment of variuos utility functions and classes for any taste.
* [writer](writer): world-to-.hdf5-container state writers.

## Writing your own modules

If our modules lack some specific functionality, you always can modify it, or create your own module. When deciding, where to place your module, think about it's use-case. If you are working on something, that isn't really fitting anywhere, use your best judgement and create a new folder with a clear and short name.

A module is a class executing one step in the pipeline. Here is the basic structure of such a module:

```python
from blenderproc.python.modules.main.Module import Module

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
This configuration object has the methods `get_int`, `get_float`, `get_bool`, `get_string`, `get_list`, `get_raw_dict`, etc. each working in the same way.
 * The first parameter specifies the key/name of the parameter to get. By using `/` it is also possible access values nested inside additional dicts (see example below).
 * The second parameter specifies the default value which is returned, if the requested parameter has not been specified inside the config file. If `None` is given, an error is thrown instead.
 
**Example:**

Config file:
```yaml
{
  "modules": [
    {
      "module": "main.Initializer",
      "config": {
        "global": {
          "output_dir": "/tmp/",
          "max_bounces": False
        }
      }
    },
    {
      "module": "renderer.NewRenderer",
      "config": {
        "max_bounces": True,
        "cycles": {
          "value": 255
        }
      }
    }
  ]
}
```

Inside the `renderer.NewRenderer` module:

```python
self.get_int("cycles/value", 42)  
# -> 255

self.get_float("pixel_aspect_x") 
# -> 1.333333333 this value is drawn from the GlobalStorage

self.get_string("output_dir", "output/") 
# -> /tmp/ this value is drawn from the GlobalStorage

self.get_bool("max_bounces") 
# -> True 

self.config.get_int("resolution_x", 512)
# ->  512

self.config.get_int("example_value") 
# -> throws an error
```

### Undo changes

In some modules it makes sense to revert changes made inside the module to not disturb modules coming afterwards (For example renderer modules should not change the state of the scene).

This often required functionality can be easily done via the `UndoAfterExecution()` with-statement:

**Example:**
```python
def run(self):
    bpy.context.scene.cycles.samples = 50
    
    with bproc.utility.UndoAfterExecution():
        bpy.context.scene.cycles.samples = 320
        
        print(bpy.context.scene.cycles.samples)
        # Outputs: 320

    print(bpy.context.scene.cycles.samples)
    # Outputs: 50
```

All changes inside the with-block are undone which could also be undone via `CTRL+Z` inside Blender.

### Between-module communication

To exchange information between modules the blender's custom properties are used (Blender allows to assign arbitrary information to scenes and objects).
So modules can read out custom properties set by earlier modules and change their behaviour accordingly.

**Example**
* The module `loader.SuncgLoader` adds the custom property `category_id` to every object 
* The module `renderer.SegMapRenderer` reads out this property and sets the segmentation color of every object correspondingly

In this way the `renderer.SegMapRenderer` can also be used without using the `loader.SuncgLoader`. 
The loader used instead just has to also set the `category_id`.
