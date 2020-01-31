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
<img src=examples/bop/icbin.png width="240" height="180"> <img src=examples/bop/tless.png width="240" height="180"> <img src=examples/bop/tless_sample.png width="240" height="180">

![](examples/suncg_basic/output-summary.png)

## General

Please refer to [DLR-RM/BlenderProc](https://github.com/DLR-RM/BlenderProc) for a general introduction on how to set up a data generation pipeline with a yaml config.

Using this package you can 
- synthetically recreate BOP datasets
- sample and render new object poses using a variety of samplers
- use collision detection and physics to generate realistic object poses
- place objects in synthetic scenes like SunCG or real scenes like Replica
This runs all modules specified in the config file in a step-by-step fashion in the configured order.

## Functionality

The following modules are already implemented and ready to use:

* Loading: *.obj, SunCG, Replica scenes.
* Lighting: Set, sample lights, automatic lighting of SunCG scenes.
* Cameras: set, sample or load camera poses from file.
* Rendering: RGB, depth, normal and segmentation images.
* Merging: .hdf5 containers.

For advanced usage which is not covered by these modules, own modules can easily be implemented.

## Examples

* [Basic scene](examples/basic/): Basic example 
* [Simple SUNCG scene](examples/suncg_basic/): Loads a SUNCG scene and camera positions from file before rendering color, normal, segmentation and a depth images.
* [SUNCG scene with camera sampling](examples/suncg_with_cam_sampling/): Loads a SUNCG scene and automatically samples camera poses in every room before rendering color, normal, segmentation and a depth images.
* [Replica dataset](examples/replica-dataset): Load a replica room, sample camera poses and render normal images.
* [COCO annotations](examples/coco_annotations): Write to a .json file containing COCO annotations for the objects in the scene.

... And much more!

## First step

Now head on to the [examples](examples) and check the README there: get some basic understanding of the config files, start exploring our examples and get a gist about writing yor own modules!

## Chane log

See our [change log](change_log.md).
