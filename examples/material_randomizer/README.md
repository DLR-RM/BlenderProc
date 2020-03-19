# Material Randomization

<div style="text-align:center">
<img src="rendering.png" alt="alt text" width=430>
<img src="rendering_switched.png" alt="alt text" width=430>
</div>

In this example we demonstrate how to switch materials  

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/material_randomizer/config.yaml examples/material_randomizer/scene.obj examples/material_randomizer/output
```

* `examples/material_randomizer/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/material_randomizer/scene.obj`: path to the object file with the basic scene.
* `examples/material_randomizer/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/material_randomizer/output/*.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light: `lighting.LightLoader` module.
* Sets two camera positions: `camera.CameraLoader` module.
* Selects materials based in the: `materials.MaterialRandomizer` module.
* Renders rgb: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

### ObjectManipulator

```yaml
{
  "module": "materials.MaterialRandomizer",
  "config": {
    "randomization_level": 0.5,
    "randomize_textures_only": False,
    "output_textures_only": False
  }
},
```

The focus of this example is the MaterialRandomizer module, which allow us to change the material of the objects randomly. 
  * Sets the `randomization_level` to 0.5, which means that a material has the change of 0.5 to be replaced with another one.
  * Set the `randomize_texture_only` and `output_texture_only` to False, which means it uses all materials not just the once with textures

It is also possible to use selectors to select the group of objects, which materials should be changed and another selector to select the objects, which materials should be used.

Check [object_manipulation](../object_manipulation) for more information about selectors.

## More examples

* [camera_sampling](../camera_sampling): More on sampling for cameras.
* [light_sampling](../light_sampling): More on sampling for lights.
