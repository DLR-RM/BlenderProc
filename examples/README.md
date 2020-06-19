# Examples

Each folder contains an example, some of those require external datasets.

## Contents

* [Examples overview](#examples-overview)

## Examples overview

Each example provides a valid configuration file that can be used for getting some sort of output, and a description.

We recommend to start with the [basic example](basic).
It will give you an idea about how, why and when certain things happen.

* [debugging](debugging): what happens during the execution of the pipeline and certain modules it is sometimes useful to use blender directly
* [camera sampling](camera_sampling): Sampling of different camera positions inside of a shape with constraints for the rotation.
* [light sampling](light_sampling): Sampling of light positions, this is the same behavior needed for the object and camera sampling.
* [object pose sampling](object_pose_sampling): Shows a more complex use of a 6D pose sampler.
* [physics_positioning](physics_positioning): Overview of an easy to use module we provide for using physics in your simulations.
* [entity manipulation](entity_manipulation): Changing various parameters of entities via selecting them through config file.
* [material_manipulation](material_manipulation): material selecting and manipulation.
* [material_randomizer](material_randomizer): object's material randomization.
* [coco annotations](coco_annotations): generating COCO annotations.
* [optical_flow](optical_flow): obtaining forward/backward flow values between consecutive key frames.
* [stereo_matching](stereo_matching): compute distance image using stereo matching.
* [on_surface_object_sampling](on_surface_object_sampling): object pose sampling on a surface.

### Benchmark for 6D Object Pose Estimation (BOP)
We provide example configs that interface with the BOP datasets.

* [bop_challenge](bop_challenge): Configs used to create the official synthetic data for the BOP challenge 2020
* [bop_object_physics_positioning](bop_object_physics_positioning): Drop BOP objects on planes and randomize materials
* [bop_object_on_surface_sampling](bop_object_on_surface_sampling): Sample upright poses on plane and randomize materials
* [bop_scene_replication](bop_scene_replication): Replicates whole scenes (object poses, camera intrinsics and extrinsics) from BOP
* [bop_object_pose_sampling](bop_object_pose_sampling): Loads BOP objects and samples object, camera and light poses

### Dataset related examples

We are providing limited dataset support, for example for ShapeNet, SceneNet, SUNCG, Replica, Rock Essentials and others.
These can be found in:
* [replica_dataset](replica_dataset)
* [shapenet](shapenet)
* [shapenet_with_scenenet](shapenet_with_scenenet)
* [shapenet_with_suncg](shapenet_with_suncg)
* [scenenet](scenenet)
* [scenenet_with_cctextures](scenenet_with_cctextures)
* [suncg_basic](suncg_basic)
* [suncg_with_cam_sampling](suncg_with_cam_sampling)
* [suncg_with_improved_mat](suncg_with_improved_mat)
* [suncg_with_object_replacer](suncg_with_object_replacer)
* [rock_essentials](rock_essentials)
