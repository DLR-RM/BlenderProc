# BlenderProc

<p align="center">
<img src="readme.jpg" alt="Front readme image" width=500>
</p>

A procedural Blender pipeline for photorealistic training image generation.

Check out our [arXiv paper](https://arxiv.org/abs/1911.01911) (we are updating it from time to time) and our [workshop paper](https://sim2real.github.io/assets/papers/2020/denninger.pdf) on sim2real transfer presented at RSS 2020.

## Overview Video

<div align="center">
<a href="http://www.youtube.com/watch?v=tQ59iGVnJWM">
<img src="BlenderProcVideoImg.jpg" alt="BlenderProc video" width=550> </a>
</div>

BlenderProc also has a complete [documentation site](https://dlr-rm.github.io/BlenderProc).

There is also an extended introduction video to BlenderProc, it covers the basics and a bit of the background story and how it all started. It can be found [here](https://www.youtube.com/watch?v=1AvY_iS6xQA).

## Contents

* [General](#general)
* [Functionality](#functionality)
* [Examples](#examples)
* [Source code](#source-code)
* [Contributions](#contributions)
* [Change log](#change-log)

## General

In general, one run of the pipeline first loads or constructs a 3D scene, then sets some camera positions inside this scene and renders different types of images (rgb, distance, normals etc.) for each of them.
The blender pipeline consists of different modules, where each of them performs one step in the described process.
The modules are selected, ordered and configured via a .yaml file.
 
To run the blender pipeline one just has to call the `run.py` script in the main directory together with the desired config file and any additional arguments.
An exemplary `config.yaml` can be found in the respective example folder.
```shell
python run.py config.yaml <additional arguments>
```

This runs all modules specified in the config file in a step-by-step fashion in the configured order.

Currently, BlenderProc officialy supports Linux and MacOS. There is also a community driven support for Windows.

## Functionality

The following modules are already implemented and ready to use:

* Loading: `*.obj`, `*.ply`, SunCG, Replica scenes, BOP datasets, etc.
* Objects: Sample object poses, apply physics and collision checking.
* Materials: Set or sample physically-based materials and textures
* Lighting: Set or sample lights, automatic lighting of SunCG scenes.
* Cameras: set, sample or load camera poses from file.
* Rendering: RGB, stereo, depth, normal and segmentation images/sequences.
* Writing: .hdf5 containers, COCO & BOP annotations.

..and many more ([docu](https://dlr-rm.github.io/BlenderProc)). For advanced/custom functionalities, you can easily write and integrate your [own modules](src/README.md#writing-your-own-modules).

## Examples

We provide a lot of [examples](examples/README.md) which explain all features in detail and should help you understand how the config files work. Exploring our examples is the best way to learn about what you can do with BlenderProc. We also provide limited support for some datasets.

* [Basic scene](examples/basic/README.md): Basic example 
* [Simple SUNCG scene](examples/suncg_basic/README.md): Loads a SUNCG scene and camera positions from file before rendering color, normal, segmentation and a distance images.
* [SUNCG scene with camera sampling](examples/suncg_with_cam_sampling/README.md): Loads a SUNCG scene and automatically samples camera poses in every room before rendering color, normal, segmentation and a distance images.
* [Replica dataset](examples/replica_dataset/README.md): Load a replica room, sample camera poses and render normal images.
* [COCO annotations](examples/coco_annotations/README.md): Write COCO annotations to a .json file for selected objects in the scene.
* [BOP Challenge](README_BlenderProc4BOP.md): Generate the pose-annotated data used at the BOP Challenge 2020

... And much more!

## Source Code

Now it's a good time to take a look at the [source code](src): All modules are there. Explore and look at the short guide about writing your own modules.

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
