# Basic scene

<p align="center">
<img src="rendering_0.jpg" alt="Front readme image" width=375>
<img src="rendering_1.jpg" alt="Front readme image" width=375>
</p>

In this example we demonstrate the basic functionality of BlenderProc.

## Usage

Execute in the BlenderProc main directory, if this is the first time BlenderProc is executed. It will automatically downloaded blender 2.91, see the config-file if you want to change the installation path:

```
python run.py examples/basic/config.yaml examples/basic/camera_positions examples/basic/scene.obj examples/basic/output
```

* `examples/basic/config.yaml`: path to the configuration file with pipeline configuration.

The three arguments afterwards are used to fill placeholders like `<args:0>` inside this config file.
* `examples/basic/camera_positions`: text file with parameters of camera positions.
* `examples/basic/scene.obj`: path to the object file with the basic scene.
* `examples/basic/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/basic/output/0.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light : `lighting.LightLoader` module.
* Loads camera positions from `camera_positions`: `camera.CameraLoader` module.
* Renders rgb, normals and distance: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

### Setup

```yaml
  "setup": {
    "blender_install_path": "/home_local/<env:USER>/blender/",
    "pip": [
      "h5py"
    ]
  }
```

* blender is installed into `/home_local/<env:USER>/blender/` where `<env:USER>` is automatically replaced by the username.
* we want to use blender 2.8 (installation is done automatically on the first run).
* inside the blender python environment the python package `h5py` should be automatically installed. These are not provided per default, but are required in order to make the `writer.Hdf5Writer` module work.

### Modules

Under `modules` we list all modules we want the pipeline to execute. The order also defines the order in which they are executed.
Every module has a name which specifies the python path to the corresponding class starting from the `src` directory and a `config` dict where we can configure the module to our needs.

#### Initializer

```yaml
 {
  "module": "main.Initializer", 
  "config": {
    "global": {
      "output_dir": "<args:2>"
    }
  }
}
```

* This module does some basic initialization of the blender project (e.q. sets background color, configures computing device, creates camera).
It also initializes the GlobalStorage, which contains two parts:
* The first one is the global config, were we are setting the `"ouput_dir"` to `"<args:2>"`, as we don't want to hardcode this path here, the `output_dir` is automatically replaced by the third argument given when running the pipeline. In the upper command the output path is set to `examples/basic/output`.
* These values are provided to all modules, but can be overwritten by the config in any module.
* The second part of the GlobalStorage is a container, which can store information over the boundaries over single modules.
* For more information on the GlobalStorage read the documentation in the class.

#### ObjectLoader

```yaml
{
  "module": "loader.ObjectLoader",
  "config": {
    "path": "<args:1>"
  }
}
```

* This module imports an .obj file into the scene.
* The path of the .obj file should be configured via the parameter `path`.
* Here we are using the second argument given, in the upper command the output path is set to `examples/basic/scene.obj`.

#### LightLoader

```yaml
{
  "module": "lighting.LightLoader",
  "config": {
    "lights": [
      {
        "type": "POINT",
        "location": [5, -5, 5],
        "energy": 1000
      }
    ]
  }
}
```

* This module creates a point light.
* The properties of this light are configured via the parameter `lights`.

#### CameraLoader

```yaml
{
  "module": "camera.CameraLoader",
  "config": {
    "path": "<args:0>",
    "file_format": "location rotation/value",
    "intrinsics": {
      "fov": 1
    }
  }
}
```

* This module imports the camera poses which defines from where the renderings should be taken.
* The camera positions are defined in a file whose path is again given via the command line (`examples/basic/camera_positions` - contains 2 cam poses).
* The file uses the following format which is defined at `file_format`.

```
location_x location_y location_z  rotation_euler_x rotation_euler_y rotation_euler_z
```

* The FOV is set via `intrinsics/fov`.
* This module also writes the cam poses into extra `.npy` files located inside the `temp_dir` (default: /dev/shm/blender_proc_$pid). This is just some meta information, so we can later clearly say which image had been taken using which cam pose.

=> Creates the files `campose_0000.npy` and `campose_0001.npy` 

#### RgbRenderer

```yaml
{
  "module": "renderer.RgbRenderer",
  "config": {
     "output_key": "colors",
     "samples": 350,
     "render_normals": True,
     "normal_output_key": "normals",
     "render_distance": True,
     "distance_output_key": "distance",
     "render_diffuse_color": True,
     "diffuse_color_output_key": "diffuse"
  }
}
```

* This module just goes through all cam poses and renders a rgb image for each of them.
* The sample amount determines the quality of the rendering, higher sampling reduces noise but increases the render time.
* The output files are stored in the defined output directory (see [Global](#Global)) and are named like `i.png` where `i` is the cam pose index
* The `output_key` config is relevant for the last module, as it defines the key at which the normal rendering should be stored inside the `.hdf5` files, we set the `output_key`, here to `colors`.

=> Creates the files `rgb_0000.png` and `rgb_0001.png`.

It also creates the normals and distance and the diffuse color image

* The normal and distance images are rendered using the `.exr` format which allows linear colorspace and higher precision
* The diffuse color image, which describes the base color of the textures, is rendered using the `.png` format.
* By default the distance image is antialiased (`"use_mist_distance"=True`).  To avoid any smoothing effects set it to `False`. 
* The `normal_output_key` config defines the key name in the `.hdf5` file, same for the `distance_output_key` and the `diffuse_color_output_key`.

=> Creates the files `normal_0000.exr` and `normal_0001.exr` and the files `distance_0000.exr` and `distance_0001.exr` and the files `diffuse_0000.png` and `diffuse_0001.png`.

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
