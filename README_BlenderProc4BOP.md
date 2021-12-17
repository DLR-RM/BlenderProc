# BlenderProc4BOP

<p align="center">
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_tless_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_03.jpg" alt="Front readme image" width=250>
</p>


## Introduction

The [Benchmark for 6D Object Pose Estimation (BOP)](https://bop.felk.cvut.cz/challenges/) [1] aims at capturing the state of the art in estimating the 6D pose, i.e. 3D translation and 3D rotation, of rigid objects from RGB/RGB-D images.
The benchmark is primarily focused on the scenario where only the 3D object models, which can be used to render synthetic training images, are available at training time. Whereas capturing and annotating real training images requires a significant effort, the 3D object models are often available or can be generated at a low cost using KinectFusion-like systems for 3D surface reconstruction.

While learning from synthetic data has been common for depth-based pose estimation methods, the same is still difficult for RGB-based methods where the domain gap between synthetic training and real test images is more severe. Specifically for the benchmark, the BlenderProc [3] team and BOP organizers [1] have therefore joined forces and prepared BlenderProc4BOP, an open-source, light-weight, procedural and photorealistic (PBR) renderer. The renderer was used to render 50K training images for each of the seven core datasets of the [BOP Challenge 2020](https://bop.felk.cvut.cz/challenges/bop-challenge-2020/) (LM, T-LESS, YCB-V, ITODD, HB, TUD-L, IC-BIN). The images can be downloaded from the website with [BOP datasets](https://bop.felk.cvut.cz/datasets/).

BlenderProc4BOP saves all generated data in the [BOP format](https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md), which allows using the visualization and utility functions from the [BOP toolkit](https://github.com/thodan/bop_toolkit).

Users of BlenderProc4BOP are encouraged to build on top of it and release their extensions.


## Image Synthesis Approach

Recent works [2,4] have shown that physically-based rendering and realistic object arrangement help to reduce the synthetic-to-real domain gap in object detection and pose estimation. In the following, we give an overview on the synthesis approach implemented in BlenderProc4BOP. Detailed explanations can be found in the [examples](#examples).

Objects from the selected BOP dataset are arranged inside an empty room, with objects from other BOP datasets used as distractors. To achieve a rich spectrum of generated images, a random PBR material from the [CC0 Textures](https://cc0textures.com/) library is assigned to the walls of the room, and light with a random strength and color is emitted from the room ceiling and from a randomly positioned point light source. This simple setup keeps the computational load low (1-4 seconds per image; 50K images can be rendered on 5 GPU's overnight).

Instead of trying to perfectly model the object materials, the object materials are randomized. Realistic object poses are achieved by dropping objects on the ground plane using the PyBullet physics engine integrated in Blender. This allows to create dense but shallow piles that introduce various levels of occlusion. When rendering training images for the LM dataset, where the objects are always standing upright in test images, we place the objects in upright poses on the ground plane.

The cameras are positioned to cover the distribution of the ground-truth object poses in test images (given by the range of azimuth angles, elevation angles and distances of objects from the camera – provided in file [dataset_params.py](https://github.com/thodan/bop_toolkit/blob/master/bop_toolkit_lib/dataset_params.py) in the BOP toolkit).


## Examples

* [bop_challenge](examples/datasets/bop_challenge): Configuration files and information on how the official synthetic data for the BOP Challenge 2020 were created.
* [bop_object_physics_positioning](examples/datasets/bop_object_physics_positioning): Drops BOP objects on a plane and randomizes materials.
* [bop_object_on_surface_sampling](examples/datasets/bop_object_on_surface_sampling): Samples upright poses on a plane and randomizes materials.
* [bop_scene_replication](examples/datasets/bop_scene_replication): Replicates test scenes (object poses, camera intrinsics and extrinsics) from the BOP datasets.
* [bop_object_pose_sampling](examples/datasets/bop_object_pose_sampling): Loads BOP objects and samples the camera, light poses and object poses in a free space.


## Results

Results of the BOP Challenge 2020 and the superiority of training with BlenderProc images over ordinary OpenGL images is shown in our paper `BOP Challenge 2020 on 6D Object Localization` [5].

## References

[1] Hodaň, Michel et al.: [BOP: Benchmark for 6D Object Pose Estimation](http://cmp.felk.cvut.cz/~hodanto2/data/hodan2018bop.pdf), ECCV 2018.  
[2] Hodaň et al.: [Photorealistic Image Synthesis for Object Instance Detection](https://arxiv.org/abs/1902.03334), ICIP 2019.  
[3] Denninger, Sundermeyer et al.: [BlenderProc](https://arxiv.org/pdf/1911.01911.pdf), arXiv 2019.  
[4] Pitteri, Ramamonjisoa et al.: [On Object Symmetries and 6D Pose Estimation from Images](https://arxiv.org/abs/1908.07640), CVPR 2020.  
[5] Hodan, Sundermeyer et al.: [BOP Challenge 2020 on 6D Object Localization](https://arxiv.org/pdf/2009.07378.pdf), ECCVW2020