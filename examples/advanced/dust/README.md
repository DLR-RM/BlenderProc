# How to apply dust to objects 
<p align="center">
<img src="../../../images/dust_rendered_example.jpg" alt="normals and color rendering of example table" width=300>
</p>


The focus of this example is adding dust to a model with blender. For this example we are using the [haven dataset](../haven/README.md).

Make sure that you have downloaded the haven dataset first, see the [haven example](../haven/README.md)

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/dust/main.py resources/haven/models/ArmChair_01/ArmChair_01_2k.blend resources/haven examples/datasets/haven/output
``` 

* `examples/advanced/dust/main.py`: path to the main python file to run.
* `resources/haven/models/ArmChair_01/ArmChair_01.blend`:  Path to the blend file, from the haven dataset, browse the model folder, for all possible options
* `resources/haven`: The folder where the `hdri` folder can be found, to load an world environment
* `examples/datasets/haven/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
blenderproc vis hdf5 examples/datasets/haven/output/*.hdf5
``` 

## Implementation

```python
# Add dust to all materials of the loaded object
for material in obj.get_materials():
    bproc.material.add_dust(material, strength=0.8, texture_scale=0.05)
```

Here `"strength"` defines the amount of dust used on the model, the range is typically from zero to one. But, values above 1.0 might also work to add a lot of dust.
The `"texture_scale"` is used to reduce the size of the generated noise texture, be aware this only works if the object already has a UV mapping. If not you can try `obj.add_uv_mapping()` for that.
