# Examples overview

Each folder contains a different example, some of those need external datasets.

If you are new with BlenderProc, check out the basic folder first, where you find an explanation on how to get started and what happens when.

## Debug

To understand what happens during the execution of the pipeline and certain modules it is sometimes useful to use blender directly. 
How to do this check out the folder [debugging](debugging).

## Sampler  
All samplers share the same structure, so understanding one of them makes it easier to understand the others as well.
Here are examples for camera, light and object pose sampling: 

* [camera sampling](camera_sampling): Sampling of different camera positions inside of a shape with constraints for the rotation
* [light sampling](light_sampling): Sampling of light positions, this is the same behavior needed for the object and camera sampling
* [object pose sampling](object_pose_sampling): Shows a more complex use of a 6D pose sampler

## Physics

We also provide a easy to use module to use physics in your simulations, check the [physics](physics_positioning) folder for more information.

## Dataset related examples

We provided already some dataset support, for example for SUNCG, Replica, CoCo Annotations and others.

These can be found in:
* [replica-dataset](replica-dataset)
* [suncg_basic](suncg_basic)
* [suncg_with_cam_sampling](suncg_with_cam_sampling)
