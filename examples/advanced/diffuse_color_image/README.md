# Diffuse color image

<p align="center">
<img src="../../../images/diffuse_color_image_rendering.jpg" alt="Front readme image" width=375>
</p>

In this example we demonstrate how to render a diffuse color image

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/diffuse_color_image/main.py examples/resources/scene.obj examples/advanced/diffuse_color_image/output
```

* `examples/advanced/diffuse_color_image/main.py`: path to the main python file to run.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/advanced/diffuse_color_image/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/advanced/diffuse_color_image/output/0.hdf5
```

## Implementation

```python
bproc.renderer.enable_diffuse_color_output()
```

Enable rendering the diffuse color image, which describes the base color of the textures.