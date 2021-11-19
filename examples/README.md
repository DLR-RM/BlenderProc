# Examples overview

We structure our examples into three different groups. We encourage everyone to start with the [basic examples](basics/README.md).

Each folder contains an example, some of those require external datasets and/or resources. Each example provides a valid configuration file(s) that can be used for getting some sort of output, a description, and, optionally, some resources.

## Contents

* [Basic Examples](#basic-examples)
* [Advanced Examples](#advanced-examples)
* [Utility Examples](#utility-examples)
* [BOP Dataset](#benchmark-for-6d-object-pose-estimation-bop)
* [Integrated Datasets Examples](#integrated-datasets-examples)

### Basic Examples 
Following examples will guide you through core functionality of BlenderProc. We recommend starting with them.

* [basic example](basics/basic/README.md): Introduction. How to run a pipeline, and how, why and when certain things happen when running one.
* [camera_sampling](basics/camera_sampling/README.md): Sampling of different camera positions inside of a shape with constraints for the rotation.
* [light_sampling](basics/light_sampling/README.md): Sampling of light poses inside of a geometrical shape.
* [entity_manipulation](basics/entity_manipulation/README.md): Changing various parameters of entities via selecting them in the config file.
* [material_manipulation](basics/material_manipulation/README.md): Material selecting and manipulation.
* [physics_positioning](basics/physics_positioning/README.md): Enabling simple simulated physical interactions between objects in the scene. 
* [semantic_segmentation](basics/semantic_segmentation/README.md): Generating semantic segmentation labels for a given scene.
* [camera_object_pose](basics/camera_object_pose/README.md): Load and render models given the intrinsics and extrinsics.

### Advanced Examples
These examples introduce usage of advanced BlenderProc modules and/or of their combinations.

* [auto_shading](advanced/auto_shading/README.md): How to change the shading mode of an object.
* [camera_depth_of_field](advanced/camera_depth_of_field/README.md): Setting an object as the camera depth of field focus point.
* [coco_annotations](advanced/coco_annotations/README.md): Generating COCO annotations in polygon or RLE format.
* [diffuse_color_image](advanced/diffuse_color_image/README.md): How to render a scene without any lighting or shading.
* [dust](advanced/dust/README.md): How to add dust on top objects, to make them look more real.
* [entity_displacement_modifier](advanced/entity_displacement_modifier/README.md): Using displacement modifiers with different textures.
* [lens_distortion](advanced/lens_distortion/README.md): Add lens distortion from camera calibration to all output images.
* [material_randomizer](advanced/material_randomizer/README.md): Randomization of materials of selected objects.
* [motion_blur_rolling_shutter](advanced/motion_blur_rolling_shutter/README.md): Generating motion blur and a rolling shutter effects.
* [object_pose_sampling](advanced/object_pose_sampling/README.md): Complex use of a 6D pose sampler.
* [on_surface_object_sampling](advanced/on_surface_object_sampling/README.md): Object pose sampling on a given surface surface.
* [optical_flow](advanced/optical_flow/README.md): Obtaining forward/backward flow values between consecutive key frames.
* [physics_convex_decomposition](advanced/physics_convex_decomposition/README.md): This examples explains how to use a faster and more stable physics simulation (only linux)
* [random_backgrounds](advanced/random_backgrounds/README.md): * Rendering an object in front of transparent background and then placing it on a random image
* [random_room_constructor](advanced/random_room_constructor/README.md): Generating rooms and populating them with objects.
* [stereo_matching](advanced/stereo_matching/README.md): Compute distance image using stereo matching.

### Utility Examples
This example is not a demonstration, but rather a tool to be used when developing your own pipeline.

* [calibration](advanced/calibration/README.md): Verifying given camera intrinsics.

### Benchmark for 6D Object Pose Estimation (BOP)
We provide example configs that interface with the BOP datasets.

* [bop_challenge](datasets/bop_challenge/README.md): Configs used to create the official synthetic data for the BOP challenge 2020
* [bop_object_physics_positioning](datasets/bop_object_physics_positioning/README.md): Drop BOP objects on planes and randomize materials
* [bop_object_on_surface_sampling](datasets/bop_object_on_surface_sampling/README.md): Sample upright poses on plane and randomize materials
* [bop_scene_replication](datasets/bop_scene_replication/README.md): Replicates whole scenes (object poses, camera intrinsics and extrinsics) from BOP
* [bop_object_pose_sampling](datasets/bop_object_pose_sampling/README.md): Loads BOP objects and samples object, camera and light poses

### Integrated Datasets Examples
We already support a lot of different datasets, check out the following examples, check out the following examples: 

* [blenderkit](datasets/blenderkit/README.md)
* [shapenet](datasets/shapenet/README.md)
* [shapenet_with_scenenet](datasets/shapenet_with_scenenet/README.md)
* [shapenet_with_suncg](datasets/shapenet_with_suncg/README.md)
* [scenenet](datasets/scenenet/README.md)
* [scenenet_with_cctextures](datasets/scenenet_with_cctextures/README.md)
* [front_3d](datasets/front_3d/README.md)
* [front_3d_with_improved_mat](datasets/front_3d_with_improved_mat/README.md)
* [rock_essentials](datasets/rock_essentials/README.md)
* [haven](datasets/haven/README.md)
* [ikea](datasets/ikea/README.md)
* [pix3d](datasets/pix3d/README.md)
* [AMASS_human_poses](datasets/amass_human_poses/README.md)
* [suncg_basic](datasets/suncg_basic/README.md)
* [suncg_with_cam_sampling](datasets/suncg_with_cam_sampling/README.md)
* [suncg_with_improved_mat](datasets/suncg_with_improved_mat/README.md)
* [suncg_with_object_replacer](datasets/suncg_with_object_replacer/README.md)
* [replica](datasets/replica/README.md)
* [rock_essentials](datasets/rock_essentials/README.md)
