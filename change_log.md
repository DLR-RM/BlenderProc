
# Planned Features

- Merge BlenderProc and BlenderProc4Bop, except README
- Add optical flow estimation
- Add depth corruption (making the perfect depth images more realistic)
- Add support for YCB objects (not just Bob)
- Add support for single object datasets


# Version History

## Version 1.2.0: 29th January 2020

- added more detailed examples to most of the important modules
- adapt CoCo annotation tools to newer Version of SegMapRenderer
- background class is now zero when doing instance segmentation
- renamed getter.Object to getter.Entity, same for ObjectManipulator is now named EntityManipulator
- entity conditions do now work with AND and OR connections
- strings are now matched with fullmatch instead of search in entity conditions
- conditions now support book custom properties
- material randomizer now supports getter.entity providers
- added UpperRegionSampler, which can sample on the up surface of the bounding box of an object
- scripts now support execution with python3.x
- physics are now saved with bool instead of active and passive
- the ObjectLoader can now load several objects at once and set their properties with `"add_properties"`
- moved more functionality in the camera sampler instead of having in specific sampler to make writing a new one easier
- added a SO3 Sampler for rotation sampling
- change the "name" of modules in the config to "module" and "provider" depending on the case
- added this changelog
- fixes:
  - fixed a problem that the check_bb_intersection did not work right in all cases (Bounding box check)
  - fixed a problem with the check_intersection fct., where the reference coordinate system was not always right.

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

