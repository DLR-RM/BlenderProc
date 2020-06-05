# BlenderProc4BOP

<p align="center">
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_tless_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_03.jpg" alt="Front readme image" width=250>
</p>

## Motivation

The [Benchmark for 6D Object Pose Estimation (BOP)](https://bop.felk.cvut.cz/challenges/) [1] is the most relevant challenge to compare the performance of both learning-based and traditional Object Pose Estimation algorithms. The 7 test datasets (LM, T-LESS, YCB-V, ITODD, HB, TUD-L, IC-BIN) represent a variety of object properties and environment conditions that are present in practice. Every year at ECCV/ICCV state-of-the-art methods are seamlessly compared using an [online evaluation system](https://bop.felk.cvut.cz/login/?next=/sub_upload/).

Capturing and annotating real training images for Object Pose Estimation requires significant effort. Therefore, the BOP Challenge is focused primarily on the more practical scenario where only the object models, which can be used to render synthetic training images, are available at training time. 

However, creating and rendering sufficiently realistic training data to bridge the sim2real gap is also challenging and time-consuming. In fact, setting up and running synthetic data generation often takes the majority of time.

Therefore, the BlenderProc [3] team and BOP organizers [1] have joined forces to create an automized, procedural data synthesis pipeline that was used to generate 350K pose-annotated RGB and depth images for the BOP challenge 2020.

## Goals of BlenderProc4BOP

- Facilitate challenge participation by providing pre-rendered, photo-realistic training data in BOP format
- Increase comparability of methods by introducing an award for learning-based methods trained solely on the provided data
- Also provide the data generation configs so that participants can generate their own data to accelerate sim2real research

For progress in the Object Pose Estimation domain, it is crucial that our evaluations are common, broad and simple. We hope that our extensions motivate researchers to contribute towards these goals.

## Data Generation

Recent works [2,4] have shown that physically-based rendering and realistic setups are beneficial for sim2real transfer in object detection and pose estimation. 

In the following we give an overview on the generation of the provided training data. Detailed explanations can be found in the [BOP examples](examples/bop_challenge).

### Environment

We decided to sample BOP objects in an empty room whose faces are randomly assigned with PBR textures to keep the computational load low while maintaining realism. This reduces the complexity of physics simulations and allows to render images in 1-4 seconds. Creating a complete synthetic BOP dataset of 50K images can thus be done overnight on 5 GPUs which hopefully also allows smaller labs to play with the data. BOP objects from other datasets are used as distractors. 

### Physically Plausible Domain Randomization

Instead of trying to perfectly model object materials, we randomize their specularity, roughness and other properties to prevent networks from relying on mismatching high frequency patterns. We emit light at random strength and color from the room ceiling and a randomly positioned point light source. Challenge participants are welcome to apply further image augmentations on the provided data.

### Object Poses

Realistic Object Poses are achieved by dropping objects on the ground plane using the PyBullet physics engine integrated in Blender. This allows us to create dense but shallow piles that resemble the test images well. Since in LineMOD, objects are standing upright on a table, we perform a sampling of upright poses on the ground plane instead. 

### Camera Poses

Through interfacing with the BOP toolkit, we automatically load the corresponding camera intrinsics and min/max raduis, azimuth and elevation ranges of the test data. Based on these parameters, we sample camera positions inside a shell around the objects. Camera rotations are determined by looking at objects near the center.

### BOP Writer

BlenderProc4BOP saves all generated synthetic data (RGB, depth, camera to object poses and camera intrinsics) in the [BOP format](https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md). This has the advantage that train and test data share the same format and the visualization and utility functions in the [bop-toolkit](https://github.com/thodan/bop_toolkit) can be directly applied.

## Examples

Now that you have an overview, head on to the examples:

* [bop_challenge](examples/bop_challenge): Configs and instructions to create the official synthetic data for the BOP challenge 2020
* [bop_object_physics_positioning](examples/bop_object_physics_positioning): Drop BOP objects on planes and randomize materials
* [bop_object_on_surface_sampling](examples/bop_object_on_surface_sampling): Sample upright poses on plane and randomize materials
* [bop_scene_replication](examples/bop_scene_replication): Replicate test scenes (object poses, camera intrinsics and extrinsics) from BOP
* [bop_object_pose_sampling](examples/bop_object_pose_sampling): Loads BOP objects and samples object, camera and light poses in free space

 ## References

[1] Hodaň, Michel et al.: [BOP: Benchmark for 6D Object Pose Estimation](http://cmp.felk.cvut.cz/~hodanto2/data/hodan2018bop.pdf), ECCV 2018.  
[2] Hodaň et al.: [Photorealistic Image Synthesis for Object Instance Detection](https://arxiv.org/abs/1902.03334), ICIP 2019.  
[3] Denninger, Sundermeyer et al.: [BlenderProc](https://arxiv.org/pdf/1911.01911.pdf), arXiv 2019.  
[4] Pitteri et al.: [On Object Symmetries and 6D Pose Estimation from Images](https://arxiv.org/abs/1908.07640), CVPR 2020.  
