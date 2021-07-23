# Diffuse color image

<p align="center">
<img src="rendering.jpg" alt="Front readme image" width=375>
</p>

In this example we demonstrate how to render a diffuse color image

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/advanced/diffuse_color_image/config.yaml examples/resources/scene.obj examples/advanced/diffuse_color_image/output
```

* `examples/advanced/diffuse_color_image/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/advanced/diffuse_color_image/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/advanced/diffuse_color_image/output/0.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light : `lighting.LightLoader` module.
* Samples camera positions randomly above the plane looking to the point of interest: `camera.CameraSampler` module.
* Renders rgb, diffuse color, normals and distance: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

#### ObjectLoader

```yaml
{
  "module": "loader.ObjectLoader",
  "config": {
    "path": "<args:0>"
  }
}
```

* This module imports an .obj file into the scene.
* The path of the .obj file should be configured via the parameter `path`.
* Here we are using the first argument given, in the upper command the output path is set to `examples/resources/scene.obj`.

#### RgbRenderer

```yaml
{
  "module": "renderer.RgbRenderer",
  "config": {
     "samples": 350,
     "render_normals": True,
     "render_distance": True,
     "render_diffuse_color": True,
  }
}
```

* This module just goes through all cam poses and renders a rgb image for each of them.
* The sample amount determines the quality of the rendering, higher sampling reduces noise but increases the render time.
* The output files are stored in the defined output directory (see [Global](#Global)) and are named like `i.png` where `i` is the cam pose index

=> Creates the files `rgb_0000.png` and `rgb_0001.png`.

It also creates the normals and distance and the diffuse color image

* The diffuse color image, which describes the base color of the textures, is rendered using the `.png` format.

=> Creates the files `diffuse_0000.png` and `diffuse_0001.png`.

In this example all of these are temporary and are used in the next module.

#### Hdf5Writer

```yaml
{
  "module": "writer.Hdf5Writer",
  "config": {
    "postprocessing_modules": {
      "distance": [
        {
          "module": "postprocessing.TrimRedundantChannels",
        }
      ]
    }
  }
}
```

* The last module now merges all the single temporary files created by the two rendering modules into one `.hdf5` file per cam pose.
* A `.hdf5` file can be seen as a dict of numpy arrays, where the keys correspond to the `output_key` defined before.
* The module can also apply some post-processing routines based on two parameters, the `output_key` (in this case `distance`) and the post-processor module, which is in this case `postprocessing.TrimRedundantChannels.py`. This reduces the distance map from 3 channels to a single channel (the other channels exist for internal reasons). 


The file `0.h5py` would therefore look like the following:

```yaml
{
  "colors": #<numpy array with pixel values read in from rgb_0000.png>,
  "distance": #<numpy array with pixel values read in from distance_0000.exr>,
  "normals": #<numpy array with pixel values read in from normals_0000.exr>,
  "diffuse": #<numpy array with pixel values read in from diffuse_0000.png>,
}
``` 

* At the end of the hdf5 writer all temporary files are deleted.
* If you want to keep them, put `"output_is_temp": False` into the config of the corresponding module or in the `Global` section.

=> Creates the files `0.h5py` and `1.h5py`
