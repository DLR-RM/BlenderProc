# Examples overview

Each folder contains an example, some of those require external datasets and/or resources. Each example provides a valid configuration file(s) that can be used for getting some sort of output, a description, and, optionally, some resources.

## Contents

* [Core Examples](#core-examples)
* [Advanced Examples](#advanced-examples)
* [Utility Examples](#utility-examples)
* [BOP Dataset](#benchmark-for-6d-object-pose-estimation-bop)
* [Integrated Datasets Examples](#integrated-datasets-examples)

### Core Examples 
Following examples will guide you through core functionality of BlenderProc. We recommend starting with them.

* [basic example](basic/README.md): Introduction. How to run a pipeline, and how, why and when certain things happen when running one.
* [basic_object_pose](basic_object_pose/README.md): Load and render models given intrinsics and extrinsics.
* [camera_sampling](camera_sampling/README.md): Sampling of different camera positions inside of a shape with constraints for the rotation.
* [light_sampling](light_sampling/README.md): Sampling of light poses inside of a geometrical shape.
* [entity_manipulation](entity_manipulation/README.md): Changing various parameters of entities via selecting them in the config file.
* [material_manipulation](material_manipulation/README.md): Material selecting and manipulation.
* [physics_positioning](physics_positioning/README.md): Enabling simple simulated physical interations between objects in the scene. 

### Advanced Examples
These examples introduce usage of advanced BlenderProc modules and/or of their combinations.

* [coco_annotations](coco_annotations/README.md): Generating COCO annotations in polygon or RLE format.
* [entity_displacement_modifier](entity_displacement_modifier/README.md): Using displacement modifiers with different textures.
* [material_randomizer](material_randomizer/README.md): Randomization of materials of selected objects.
* [motion_blur_rolling_shutter](motion_blur_rolling_shutter/README.md): Generating motion blur and a rolling shutter effects.
* [object_pose_sampling](object_pose_sampling/README.md): Complex use of a 6D pose sampler.
* [on_surface_object_sampling](on_surface_object_sampling/README.md): Object pose sampling on a given surface surface.
* [optical_flow](optical_flow/README.md): Obtaining forward/backward flow values between consecutive key frames.
* [random_room_constructor](random_room_constructor/README.md): Generating rooms and populating them with objects.
* [semantic_segmentation](semantic_segmentation/README.md): Generating semantic segmentation labels for a given scene.
* [stereo_matching](stereo_matching/README.md): Compute distance image using stereo matching.

### Utility Examples
These examples are not demonstrations, but rather tools to be used when developing or debugging your own pipeline.

* [debugging](debugging/README.md): Using Blender directly to debug given pipeline, gives insight into what happens during the execution of the pipeline.
* [calibration](calibration/README.md): Verifying given camera intrinsics.

### Benchmark for 6D Object Pose Estimation (BOP)
We provide example configs that interface with the BOP datasets.

* [bop_challenge](bop_challenge/README.md): Configs used to create the official synthetic data for the BOP challenge 2020
* [bop_object_physics_positioning](bop_object_physics_positioning/README.md): Drop BOP objects on planes and randomize materials
* [bop_object_on_surface_sampling](bop_object_on_surface_sampling/README.md): Sample upright poses on plane and randomize materials
* [bop_scene_replication](bop_scene_replication/README.md): Replicates whole scenes (object poses, camera intrinsics and extrinsics) from BOP
* [bop_object_pose_sampling](bop_object_pose_sampling/README.md): Loads BOP objects and samples object, camera and light poses

### Integrated Datasets Examples
We are providing limited dataset support with following examples.

* [replica_dataset](replica_dataset/README.md)
* [shapenet](shapenet/README.md)
* [shapenet_with_scenenet](shapenet_with_scenenet/README.md)
* [shapenet_with_suncg](shapenet_with_suncg/README.md)
* [scenenet](scenenet/README.md)
* [scenenet_with_cctextures](scenenet_with_cctextures/README.md)
* [front_3d](front_3d/README.md)
* [front_3d_with_improved_mat](front_3d_with_improved_mat/README.md)
* [rock_essentials](rock_essentials/README.md)
* [haven_dataset](haven_dataset/README.md)
* [ikea](ikea/README.md)
* [pix3d](pix3d/README.md)
* [AMASS](amass_human_poses/README.md)
* [suncg_basic](suncg_basic/README.md)
* [suncg_with_cam_sampling](suncg_with_cam_sampling/README.md)
* [suncg_with_improved_mat](suncg_with_improved_mat/README.md)
* [suncg_with_object_replacer](suncg_with_object_replacer/README.md)
