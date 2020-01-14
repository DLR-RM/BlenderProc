# BlenderProc4BOP

Procedural Annotated Data Generation using the [Blender](https://www.blender.org/) API.

BlenderProc4BOP extends [DLR-RM/BlenderProc](https://github.com/DLR-RM/BlenderProc) with interfaces to the [BOP datasets](https://bop.felk.cvut.cz/datasets/) and provides code to generate photo-realistic training data for Object Instance Segmentation and Pose Estimation methods. 

Note: This library is under active development. We are open for new contributors and happy to accept pull requests e.g. defining new modules.

The corresponding arxiv paper: https://arxiv.org/2901471

<!-- 
Citation: 
```
@article{blenderproc2019,
	title={},
	author={},
	journal={arXiv preprint arXiv:1910.00199},
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

You can render normals, RGB and depth and  extract class + instance segmentation labels and pose annotations. All generated data and labels are saved in compressed hdf5 files.

You can parametrize both, loaders and samplers for  
- object poses
- lights
- cameras
- materials
- whole datasets 

Because of the modularity of this package and the sole dependency on the Blender API, it is very simple to insert your own module. Also, any new feature introduced in Blender can be utilized here.

## Usage with BOP

First make sure that you have downloaded a [BOP dataset](https://bop.felk.cvut.cz/datasets/) in the original folder structure. Also please clone the [BOP toolkit](https://github.com/thodan/bop_toolkit).

### Configure `examples/bop/config_sample.yaml`

Set the `blender_install_path` where Blender 2.81 should be installed and add the path to your bop_toolkit clone to `sys_paths`.

## Start the data generation
In general, to run a BlenderProc pipeline and install dependencies, you run:

```
python run.py config.yaml <additional arguments>
```

To run a BOP example where we sample object and cameras, we additionally need to specify the paths to the bop dataset and an output directory:

```
python run.py examples/bop/config_sample.yaml /path/to/bop/dataset /path/to/output_dir
```

After the generation has finished you can view the generated data using

```
python scripts/visHdf5Files.py /path/to/output/0.hdf5

```
python scripts/visHdf5Files.py /path/to/output/0.hdf5
```

## Generate Random Object/Camera/Light Poses

Go to [examples/bop/README.md](examples/bop/README.md) for a more detailed explanation and a second example where we replicate BOP scenes.

## Customized Modules

You can create realistic synthetic data and labels by combining and parametrizing existing modules. Use the documented examples to build your own config.

Parametrize lighting.LightSampler, camera.CameraSampler, or object.ObjectPoseSampler with existing sampling functions (e.g. uniform shell, sphere or cube). Use loaders like lighting.LightLoader and camera.CameraLoader to load poses and other parameters from a file or from the config directly. Sample object poses using physics like in examples/physics_positioning. Sample objects in synthetic or real scene environments like SunCG or Replica.

Besides parametrizing existing modules, you can also create your own modules (see [Writing Modules](https://github.com/DLR-RM/BlenderProc#writing-modules)). New modules can either combine existing modules with some logic (e.g. [composite/CameraObjectSampler](composite/CameraObjectSampler)) or create completely new functionality based on the Blender API.


