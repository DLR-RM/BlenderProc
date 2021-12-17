# Basic scene

<p align="center">
<img src="../../../images/basic_rendering_0.jpg" alt="Front readme image" width=375>
<img src="../../../images/basic_rendering_1.jpg" alt="Front readme image" width=375>
</p>

In this example we demonstrate the basic functionality of BlenderProc.

## Usage

Execute in the BlenderProc main directory, if this is the first time BlenderProc is executed. It will automatically download blender, see the CLI arguments if you want to change the installation path:

```
blenderproc run examples/basics/basic/main.py examples/resources/camera_positions examples/resources/scene.obj examples/basics/basic/output
```

* `examples/basics/basic/main.py`: path to the python file with pipeline configuration.

The three arguments afterwards are used by the `argparser` at the top of the `main.py` file:
* `examples/resources/camera_positions`: text file with parameters of camera positions.
* `examples/resources/scene.obj`: path to the object file with the basic scene.
* `examples/basics/basic/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/basics/basic/output/0.hdf5
```

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module.
* Creates a point light : `lighting.LightLoader` module.
* Loads camera positions from `camera_positions`: `camera.CameraLoader` module.
* Renders rgb, normals and depth: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

### Setup

```python
import blenderproc as bproc
```

This sets up the `blenderproc` environment. `blenderproc` has to be the first import. This import already installs blender and all necessary pip packages.

```python
bproc.init()
```

This init does some basic initialization of the blender project (e.q. sets background color, configures computing device, creates a camera).

#### Object loading

```python
# load the objects into the scene
objs = bproc.loader.load_obj(args.scene)
```

* This call imports an .obj file into the scene.
* The path of the `.obj` is given via the `args.scene` value.
* Here we are using the second argument given to the `blenderproc` run, in the upper command. The output path is set to `examples/resources/scene.obj`.

#### Light loading 

```python
# define a light and set its location and energy level
light = bproc.types.Light()
light.set_type("POINT")
light.set_location([5, -5, 5])
light.set_energy(1000)
```

Here a point light is created. The location and energy are set via the `set_location` and `set_energy` fcts.

#### Camera loading

```python
# define the camera resolution
bproc.camera.set_resolution(512, 512)

# read the camera positions file and convert into homogeneous camera-world transformation
with open(args.camera, "r") as f:
    for line in f.readlines():
        line = [float(x) for x in line.split()]
        position, euler_rotation = line[:3], line[3:6]
        matrix_world = bproc.math.build_transformation_mat(position, euler_rotation)
        bproc.camera.add_camera_pose(matrix_world)
```

First the camera resolution is set to `512` by `512`. 
After that the camera pose file is parsed and a matrix to world is calculated based on the extracted position and rotation. 
This is then set via the `bproc.camera.add_camera_pose(matrix_world)` fct call. 
Be aware that each of these calls uses the created camera in the `init` step and adds a new key frame saving its pose.

The file format here is: 

```
location_x location_y location_z  rotation_euler_x rotation_euler_y rotation_euler_z
```


=> Creates the files `campose_0000.npy` and `campose_0001.npy` 

#### Rgb rendering

```python
# activate normal and depth rendering
bproc.renderer.enable_depth_output(activate_antialiasing=False)
bproc.renderer.enable_normals_output()
bproc.renderer.set_noise_threshold(0.01)  # this is the default value

# render the whole pipeline
data = bproc.renderer.render()
```

First we enable that `blenderproc` also generates the `normals` and the `distance` for each color image.
Furthermore, we set the desired noise threshold in our image. 
A lower noise threshold will reduce the noise in the image, but increase the rendering time. 
The default value is `0.01`, this should work for most applications. 

=> Creates the files `rgb_0000.png` and `rgb_0001.png` in the temp folder.

It also creates the normals and depth 

* The normal and depth images are rendered using the `.exr` format which allows linear colorspace and higher precision
* Here, the depth image is not antialiased, meaning that for each pixel the depth in this pixel is not aggregated over its surface. While distance and depth images sound similar, they are not the same: In [distance images](https://en.wikipedia.org/wiki/Range_imaging), each pixel contains the actual distance from the camera position to the corresponding point in the scene.  In [depth images](https://en.wikipedia.org/wiki/Depth_map), each pixel contains the distance between the camera and the plane parallel to the camera which the corresponding point lies on.

=> Creates the files `normal_0000.exr` and `normal_0001.exr` and the files `distance_0000.exr` and `distance_0001.exr`.

In this example all of these are temporary and are read in directly after rendering and deleted in the temp folder. 
These are then packed into a dictionary and returned and saved in the `data` variable.

FAQ: Why are they stored on disc if we read them directly in again? 
- Blender offers no other option than to first save them to disc and afterwards reading them in again.

#### Hdf5 Writing 

```python
# write the data to a .hdf5 container
bproc.writer.write_hdf5(args.output_dir, data)
```

* The last module now merges all images created by the rendering call into one `.hdf5` file per cam pose.
* A `.hdf5` file can be seen as a dict of numpy arrays.

The file `0.h5py` would therefore look like the following:

```yaml
{
  "colors": #<numpy array with pixel values read in from rgb_0000.png>,
  "depth": #<numpy array with pixel values read in from depth_0000.exr>,
  "normals": #<numpy array with pixel values read in from normals_0000.exr>,
}
``` 

=> Creates the files `0.h5py` and `1.h5py`

# More Modules

Well done, how about another example on [camera_sampling](../camera_sampling/README.md) or are you more interested in [object manipulation](../entity_manipulation/README.md)?
