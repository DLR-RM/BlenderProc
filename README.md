# BlenderProc2

[![Documentation](https://img.shields.io/badge/documentation-passing-brightgreen.svg)](https://dlr-rm.github.io/BlenderProc/)
[![Open In Collab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DLR-RM/BlenderProc/blob/main/examples/basics/basic/basic_example.ipynb)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<p align="center">
<img src="https://user-images.githubusercontent.com/6104887/137109535-275a2aa3-f5fd-4173-9d16-a9a9b86f66e7.gif" alt="Front readme image" width=100%>
</p>

A procedural Blender pipeline for photorealistic rendering.

[Documentation](https://dlr-rm.github.io/BlenderProc) | [Tutorials](#tutorials) | [Examples](#examples) | [ArXiv paper](https://arxiv.org/abs/1911.01911) | [Workshop paper](https://sim2real.github.io/assets/papers/2020/denninger.pdf)
## Features

* Loading: `*.obj`, `*.ply`, `*.blend`, BOP, ShapeNet, Haven, 3D-FRONT, etc.
* Objects: Set or sample object poses, apply physics and collision checking.
* Materials: Set or sample physically-based materials and textures
* Lighting: Set or sample lights, automatic lighting of 3D-FRONT scenes.
* Cameras: Set, sample or load camera poses from file.
* Rendering: RGB, stereo, depth, normal and segmentation images/sequences.
* Writing: .hdf5 containers, COCO & BOP annotations.


## Installation

### Via pip

The simplest way to install blenderproc is via pip:

```bash
pip install blenderproc
```

### Git clone

If you need to make changes to blenderproc or you want to make use of the most recent version on the main-branch, clone the repository:

```bash
git clone https://github.com/DLR-RM/BlenderProc
```

To still make use of the blenderproc command and therefore use blenderproc anywhere on your system, make a local pip installation:

```bash
cd BlenderProc
pip install -e .
```

## Usage

BlenderProc has to be run inside the blender python environment, as only there we can access the blender API. 
Therefore, instead of running your script with the usual python interpreter, the command line interface of BlenderProc has to be used.

```bash
blenderproc run <your_python_script>
```

In general, one run of your script first loads or constructs a 3D scene, then sets some camera poses inside this scene and renders different types of images (RGB, distance, semantic segmentation, etc.) for each of those camera poses.
In the usual case, to create a big and diverse dataset, you therefore run your script multiple times, each time producing 5-20 images.
With a little more experience, it is also possible to render multiple times in one script call, read [here](docs/tutorials/key_frames.md#render-multiple-times) how this is done.

## Quickstart

Create a python script `quickstart.py` with the following content:

```python
import blenderproc as bproc
import numpy as np

bproc.init()

# Create a simple object:
obj = bproc.object.create_primitive("MONKEY")

# Create a point light next to it
light = bproc.types.Light()
light.set_location([2, -2, 0])
light.set_energy(300)

# Set the camera to be in front of the object
cam_pose = bproc.math.build_transformation_mat([0, -5, 0], [np.pi / 2, 0, 0])
bproc.camera.add_camera_pose(cam_pose)

# Render the scene
data = bproc.renderer.render()

# Write the rendering into an hdf5 file
bproc.writer.write_hdf5("output/", data)
```

Now run the script via:

```bash
blenderproc run quickstart.py
```

BlenderProc now creates the specified scene and renders the image into `output/0.hdf5`.
To visualize that image, simply call:

```bash
blenderproc vis hdf5 output/0.hdf5
```

Thats it! You rendered your first image with BlenderProc!

### Debugging

To understand what is actually going on, BlenderProc has the great feature of visualizing everything inside the blender UI.
To do so, simply call your script with the `debug` instead of `run` subcommand:
```bash
blenderproc debug quickstart.py
```

Now the Blender UI opens up, the scripting tab is selected and the correct script is loaded.
To start the BlenderProc pipeline, one now just has to press `Run BlenderProc` (see red circle in image).
As in the normal mode, print statements are still printed to the terminal.

<p align="center">
<img src="images/debug.jpg" alt="Front readme image" width=500>
</p>

The pipeline can be run multiple times, as in the beginning of each run the scene is cleared.

## What to do next?

As you now ran your first BlenderProc script, your ready to learn the basics:

### Tutorials

Read through the tutorials, to get to know with the basic principles of how BlenderProc is used:

1. [Loading and manipulating objects](docs/tutorials/loader.md)
2. [Configuring the camera](docs/tutorials/camera.md)
3. [Rendering the scene](docs/tutorials/renderer.md)
4. [Writing the results to file](docs/tutorials/writer.md)
5. [How key frames work](docs/tutorials/key_frames.md)
6. [Positioning objects via the physics simulator](docs/tutorials/physics.md)

### Examples

We provide a lot of [examples](examples/README.md) which explain all features in detail and should help you understand how BlenderProc works. Exploring our examples is the best way to learn about what you can do with BlenderProc. We also provide support for some datasets.

* [Basic scene](examples/basics/basic/README.md): Basic example, this is the ideal place to start for beginners
* [Camera sampling](examples/basics/camera_sampling/README.md): Sampling of different camera positions inside of a shape with constraints for the rotation.
* [Object manipulation](examples/basics/entity_manipulation/README.md): Changing various parameters of objects.
* [Material manipulation](examples/basics/material_manipulation/README.md): Material selecting and manipulation.
* [Physics positioning](examples/basics/physics_positioning/README.md): Enabling simple simulated physical interactions between objects in the scene.
* [Semantic segmentation](examples/basics/semantic_segmentation/README.md): Generating semantic segmentation labels for a given scene.
* [BOP Challenge](README_BlenderProc4BOP.md): Generate the pose-annotated data used at the BOP Challenge 2020
* [COCO annotations](examples/advanced/coco_annotations/README.md): Write COCO annotations to a .json file for selected objects in the scene.

and much more, see our [examples](examples/README.md) for more details.


## Contributions

Found a bug? help us by reporting it. Want a new feature in the next BlenderProc release? Create an issue. Made something useful or fixed a bug? Start a PR. Check the [contributions guidelines](CONTRIBUTING.md).

## Change log

See our [change log](change_log.md). 

## Citation 

If you use BlenderProc in a research project, please cite as follows:

```
@article{denninger2019blenderproc,
  title={BlenderProc},
  author={Denninger, Maximilian and Sundermeyer, Martin and Winkelbauer, Dominik and Zidan, Youssef and Olefir, Dmitry and Elbadrawy, Mohamad and Lodhi, Ahsan and Katam, Harinandan},
  journal={arXiv preprint arXiv:1911.01911},
  year={2019}
}
```

---

<div align="center">
  <a href="https://www.dlr.de/EN/Home/home_node.html"><img src="images/logo.svg" hspace="3%" vspace="60px"></a>
</div>
