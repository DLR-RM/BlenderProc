
# Planned Features

- Add support for YCB objects (not just Bob)
- Add optical flow estimation
- Add depth corruption (making the perfect depth images more realistic)
- Merge BlenderProc and BlenderProc4Bop, except README


# Version History

## Version 1.1.0: 16th January 2020

- Added provider, which can be executed inside of different modules, examples:
    - Samplers of values
    - Getters of objects, specified on one condition (for example the name)
- Added object manipulators, these can change selected objects attributes and custom properties
- Added physics positioning, objects can be either "active" or "passive" and then interact with each other
- Added ObjectPoseSampler sampled collision free poses of all objects
- Added one ObjectLoader, which deals with all kinds of objects
- Added a camera object sampler to sample cameras and objects at the same time
- Redone the SegMapRenderer to fix bug in instance and class segmentation
- Added coco annotations writer
- Added version number to config files
- Added more documentation 
- Added more examples

## Version 1.0.0: 25th October 2019

- Added Pipeline, Modules and Config
- Added CameraModules, with different sampler for SUNCG and replica 
- Added LightModules, with different samplers also for SUNCG
- Added Loader for objects
- Added Loader for replica and SUNCG
- Added Hdf5 Writer
- Added camera-, light-, object state writer
- Added MaterialRandomizer
- Added Shell-, Sphere- and Uniform3DSampler
- Added debug script

