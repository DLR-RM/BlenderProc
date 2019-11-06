# BlenderProc4BOP

Procedural Annotated Data Generation using the [Blender](https://www.blender.org/) API.

BlenderProc4BOP interfaces with the [BOP datasets](https://bop.felk.cvut.cz/datasets/) and lets you generate photo-realistic training data, e.g. for Object Instance Segmentation and Pose Estimation methods. 

Note: This library is usable but is still under active development. We are open for new contributors and happy to accept pull requests that improve the code or simply introduce a new module / dataset.

The corresponding paper can be found here: https://arxiv.org/abs/1911.01911

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

Please refer to [DLR-RM/BlenderProc](https://github.com/DLR-RM/BlenderProc) for a general introduction on how to set up a data generation pipeline.

Using this package you can 
- synthetically recreate BOP datasets
- sample and render new object poses using a variety of samplers
- use collision detection and physics to generate realistic object poses
- place objects in synthetic scenes like SunCG or real scenes like Replica

You can render normals, RGB and depth and  extract class + instance segmentation labels and pose annotations. All generated data is saved in a compressed hdf5 file.

You can parametrize both, loaders and samplers for  
- object poses
- lights
- cameras
- materials
- whole datasets 

Because of the modularity of this package and the sole dependency on the Blender API, it is very simple to insert your own module. Also, any new feature introduced in Blender can be utilized here.

## Usage with BOP

First make sure that you have downloaded a [BOP dataset](https://bop.felk.cvut.cz/datasets/) in the original folder structure. Also please clone the [BOP toolkit](https://github.com/thodan/bop_toolkit).

### Configure examples/bop/config.yaml

 Set the blender_install_path where Blender 2.80 should be installed and the path to your bop_toolkit clone.

Select the scene_id you want to recreate in loader.BopLoader and set split to "test" or "val" depending on the considered BOP dataset.

## Start the data generation
In general, to run a BlenderProc pipeline and install dependencies, you run:

```
python run.py config.yaml <additional arguments>
```

To run the bop example, we need to specify the paths to the bop dataset and an output directory:

```
python run.py examples/bop/config.yaml /path/to/bop/dataset /path/to/output_dir
```

Note: Initial loading can take some time, in the config you can adjust the samples of the renderer to trade-off quality and render time.

After the generation has finished you can view the generated data using

```
python scripts/visHdf5Files.py /path/to/output/0.hdf5
```

## Generate Random Object/Camera/Light Poses

In examples/bop/config.yaml simply comment in the object.PositionSampler and run the script again. Now the objects of a scene are rendered at random positions uniformly distributed inside a 3D block at random orientations. You can parametrize different samplers, have a look at utility/sampler. If a sampled object collides with another object, it is resampled.

The same samplers can also be used to sample new camera and light poses. Simply define a lighting.LightSampler or camera.CameraSampler in your config. You can also use a lighting.LightLoader and camera.CameraLoader to load poses from a file or the config directly.




