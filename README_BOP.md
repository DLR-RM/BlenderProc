# BlenderProc4BOP

Procedural Annotated Data Generation using the [Blender](https://www.blender.org/) API.

BlenderProc4BOP extends [DLR-RM/BlenderProc](https://github.com/DLR-RM/BlenderProc) with interfaces to the [BOP datasets](https://bop.felk.cvut.cz/datasets/) and provides code to generate photo-realistic training data for Object Instance Segmentation and Pose Estimation methods. 

Note: This library is under active development. We are open for new contributors and happy to accept pull requests e.g. defining new modules.

The corresponding arxiv paper: https://arxiv.org/abs/1911.01911

<!-- 
Citation: 
```
@article{blenderproc2019,
	title={BlenderProc},
	author={Denninger, Maximilian and Sundermeyer, Martin and Winkelbauer, Dominik and Zidan, Youssef  and Olefir, Dmitry and Elbadrawy, Mohamad and Lodhi, Ahsan and Katam, Harinandan},
	journal={arXiv preprint arXiv:1911.01911},
	year={2019}
}
``` -->
<img src=examples/bop_scene_replication/icbin.png width="240" height="180"> <img src=examples/bop_scene_replication/tless.png width="240" height="180"> <img src=examples/bop_sampling/tless_sample.png width="240" height="180">

![](examples/suncg_basic/output-summary.png)

## General

Please refer to [DLR-RM/BlenderProc](https://github.com/DLR-RM/BlenderProc) for a general introduction on how to set up a data generation pipeline with a yaml config.

Using this package you can 
- synthetically recreate BOP datasets
- sample and render new object poses using a variety of samplers
- use collision detection and physics to generate realistic object poses
- place objects in synthetic scenes like SunCG or real scenes like Replica

Render normals, RGB, stereo and depth. Extract class and instance segmentation labels and pose annotations. All generated data and labels are saved in compressed hdf5 files or automatically converted into COCO annotations.

You can parametrize a variety of loaders and samplers for  
- object poses
- lights
- cameras
- materials

Because of the modularity of this package and the sole dependency on the Blender API, it is very simple to insert your own module. Also, any new feature introduced in Blender can be utilized here.

## Usage with BOP

First make sure that you have downloaded a [BOP dataset](https://bop.felk.cvut.cz/datasets/) in the original folder structure. Also please clone the [BOP toolkit](https://github.com/thodan/bop_toolkit).

We provide two example configs that interface with the BOP datasets:

* [bop_scene_replication](examples/bop_scene_replication/README.md): Replicates whole scenes (object poses, camera intrinsics and extrinsics) of BOP datasets
* [bop_sampling](examples/bop_sampling/README.md):
 Loads BOP objects and samples object, camera and light poses

## Customize and write new modules

You can create realistic synthetic data and labels by combining and parametrizing existing modules. Use the documented [examples](examples/README.md) to build your own config.

Parametrize lighting.LightSampler, camera.CameraSampler, or object.ObjectPoseSampler with existing sampling functions (e.g. uniform shell, sphere or cube). Use loaders like lighting.LightLoader and camera.CameraLoader to load poses and other parameters from a file or from the config directly. Sample object poses using physics like in [examples/physics_positioning](examples/physics_positioning). Sample objects in synthetic or real scene environments like SunCG or Replica.

Besides parametrizing existing modules, you can also create your own modules (see [Writing Modules](https://github.com/DLR-RM/BlenderProc#writing-modules)). New modules can either combine existing modules with some logic (e.g. [composite/CameraObjectSampler](composite/CameraObjectSampler)) or create completely new functionality based on the Blender API.


