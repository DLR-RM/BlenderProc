# Material Randomization

<div style="text-align:center">
<img src="../../../images/material_randomizer_rendering.jpg" alt="alt text" width=430>
<img src="../../../images/material_randomizer_rendering_switched.jpg" alt="alt text" width=430>
</div>

In this example we demonstrate how to switch materials.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/material_randomizer/main.py examples/resources/scene.obj examples/advanced/material_randomizer/output
```

* `examples/advanced/material_randomizer/main.py`: path to the main python file to run.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/advanced/material_randomizer/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis_hdf5 examples/advanced/material_randomizer/output/*.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light: `lighting.LightLoader` module.
* Sets two camera positions: `camera.CameraLoader` module.
* Selects materials based in the: `manipulators.EntityManipulator` module.
* Renders rgb: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

### Entity Manipulator

```python
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
          "randomization_level": 0.5
        }
      }
    }
```

The focus of this example is the fucntionality of the `manupulators.EntityManipulator` module, which allows us to change the material of the objects randomly. 
 * Sets the `randomization_level` to 0.5, which means that a material has the change of 0.5 to be replaced with another one.

Select the pool of objects for which we randimize materials with certain probability, and select material substitute. If no `getter.Material` is called, a random material from all of the materials will be used as substitution. 
