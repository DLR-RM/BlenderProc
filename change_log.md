
# Planned Features

- Adding a complete python API and phasing out the `.yaml` files (Goal for 2.0.0)
- Add support for all YCB objects (not just BOP)
- Add support for more object datasets (ideas are welcomed, just open an issue with a dataset you want to see integrated)
- Add support for BlenderKit (download is done, easy using is still missing)
- Improve the documentation 

# Version History

## Version 1.9.0 10th February 2021
- all `Loader` now support setting the `add_material_properties` of the newly loaded objects
- each new `.hdf5` file, will contain the git commit hash of BlenderProc
- introduce `LightUtility` -> this fulfills our long time goal giving BlenderProc a python API
- changed the default stereo mode from `OFFAXIS` to `PARALLEL`
- adapt to the changes made to 3D Front, as 3D Front does not have a version number, we support the newest version and a version from Summer 2020, if you have errors please open an issue
- `getter.Material` can now return all materials of a list of objects, selected via the `getter.Entity`
- add a `cf_add_*` fct to the MaterialManipulator, which works similar to the `cf_set_*` fct.
- add `check_empty` to `getter.Entity` and to `getter.Material` to throw an error if the returned list is empty
- added a `cf_add_uv_mapping/forced_recalc_of_uv_maps` option to force to recalculate the uv map of materials, which already have a uv map
- added option that randomized materials in `cf_randomize_materials` are added to objects without any materials
- change that `cf_randomize_materials` inside the `EntityManipulator` now deals with lists and not single elements as before
- add auto download for the imageio library, if that fails an exception is thrown with instructions on how to do this yourself
- `CameraInterface` now supports setting poses for a certain frame -> also needed for the python API
- changed the `depth_scale` default value in the BopWriter from `0.1` to `1.0`, added an option to change via the config
- changed the `ignore_dist_thres` default value in the BopWriter from `5.0` to `100.0`
- improved the ShapeNet example, by adding a ShapeNetWriter, which saves which object was used in the `.hdf5` container
- fixes a bug with the separation of ceilings and floor objects in SceneNet scenes 
- fix a bug, where the `add_alpha_channel_to_texture` fct. couldn't deal with empty material sockets
- fix the `pyhsics_positioning` example by using the `collision_shape="MESH"`
- fix a bug, where empty material_sockets would have been returned in the `getter.Material`
- fix `vis_coco_annotation` script, didn't work anymore after the segmentation map rewrite

## Version 1.8.2: 27th January 2021
- added stereo mode to SegMapRenderer
- switched to using imageio for reading images, as the blender image loading API does not support .exr files written in stereo mode
- added option to write world-to-cam transformations to the BopWriter
- CocoAnnotationWriter does now in the polygon format not write empty segmentation lists anymore and uses iscrowd:0
- type hints are now added to the generated documentation
- extracted reusable rendering code from the renderer modules into utility classes 

## Version 1.8.1: 14th January 2021
- fixed a bug in the WriterInterface
- fixed cc_texture downloader script in the case of weird urls
- fixed creating the ceiling when there are rounding errors in the vertices coordinates

## Version 1.8.0: 11th December 2020
- massively improve the documentation, by adding using github pages for our documentation: https://dlr-rm.github.io/BlenderProc/index.html
- add a RandomRoomConstructor: 
  - This module can generate random floor plans of single rooms, with arbitrary extrusions.
  - It can also randomly place loaded objects without collision inside of the room
  - By using CCTexture it is also possible to assign random materials to the floor, wall and ceiling
- remove the SceneNetLighting module and replace it with the SurfaceLighting module, to make it more general
- add support for the haven websites and add an example and corresponding loaders:
  - The haven environment website: https://hdrihaven.com/
  - The haven model website: https://3dmodelhaven.com/
  - The haven texture website: https://texturehaven.com/
- add option to the CameraSampler to ensure that a certain object is always in the camera view
- improve the FloorExtractor to extract the floor and ceiling in SceneNet and other scenarios
- improve the skin tones for AMASSLoader
- add a proper scaling to the ikea dataset, by converting all files into SI units
- fix the ikea dataset downloading, by removing and splitting broken pieces, we advise to redownload the dataset

## Version 1.7.0: 1st December 2020
- switch to blender 2.91
- added an example of how to set object poses via a transformation matrix and set camera extrinsics / intrinsics via a transformation matrix and a K matrix
- added camera utility class which makes it easier to set and retrieve intrinsics via any K matrix
- added loader for Pix3D dataset
- added loader for AMASS dataset
- added loader for the ikea dataset
- added community driven support for Windows
- added motion blur and rolling shutter support
- fixed collision checks between meshes, so the ObjectPoseSampler is not generating colliding object poses anymore
- fixed cleanup of temporary directories in the case of an error
- set pixel origin to the center of a pixel, slightly affecting intrinsics and depth outputs
- fixed coco annotations if background is not visible
- added support for transparent background
- fixed wrong image size in coco annotations
- fixed blender proc if non-english language is configured
- when loading ply files a default material is now added
- fixed setting matrix_world via the entity manipulator
- fixed the scenenet examples (corrects physics positioning and camera sampling)

## Version 1.6.1: 25th August 2020
- fixed bbox computation in the Coco Annotations
- fixed visualization of Coco Annotations
- add set properties fct. to BlenderLoader
- adds a script to download all materials from BlenderKit (not used yet)

## Version 1.6.0: 24th July 2020
- added an `TextureLoader`, which can load images and store them as blender textures
- added a provider to access these loaded textures
- removed the `MaterialRandomizer`
- moved the whole functionality from the `MaterialRandomizer` to the `EntityManipulator`
- fixed a bug in the SUNCG material loading, where for a few objects the diffuse material was confused with an alpha material
- add set_properties for `Front3DLoader`
- fixed the `min_interest_score` that it works with more than just SUNCG
- fix a bug in the visHdf5 scripts with distance maps which had several channels
- improved documentation for `min_interest_score` and `check_pose_novelty_translation`

## Version 1.5.1: 17th July 2020
- adding support for 3D-Front: https://tianchi.aliyun.com/specials/promotion/alibaba-3d-scene-dataset
- added to example on how to use 3D-Front
- fixed visualization of newly generated SegMapRenderer results
- fixed combining several coco annotations
- added option for the "class" key for default values in the SegMapRenderer
- fixed a bug in the SegMapRenderer when used in debug mode

## Version 1.5.0: 14th July 2020
- rename depth to distance (this is the difference between taking at each pixel the Z coordinate (in the camera coordinate system) or the distance from the optical center, as sensors usually produce depth and not distance, we changed this)
- create postprocessing module to calculate the depth out of the distance image
- rewriting of the SegMapRenderer, it now supports the mapping of any attribute or custom property of an object to an image or a csv file
- reworking of the used coco examples to better work with this new SegMapRenderer
- adapting CocoAnnotationsWriter to write category_ids which must be defined in a Loader or in a .blend file
- adding support for a supercategory inside of the coco annotations tool (useful for bop dataset names)
- add texture provider, which can generate random textures, which can be used in a displacement modifier
- added to the EntityManipulator: 
  - option to automatically generate a UV mapping for an object
  - added option for displacement modifier adding to objects
  - added an example for the entity_displacement_modifier usage
- the sampler.Value now supports gaussian sampling
- reworked some parts of the Hdf5Writer, to better work with depth and distance
- added a check to the CocoUtility to avoid that the bounding box has a area of zero
- remove the provider.ContentGetter as it was confusing, now it works directly without it
- add an Interface in the naming of some modules, if they are not supposed to be run by the pipeline directly
- change the sample amount for the FlowRenderer to 1 as a higher sampling density integrates over several objects in one pixel
- added a step function in the alpha mode of the renderer to avoid artifacts, when rendering semantic segmentations
- support for setting different fx/fy values in the camera module
- remove the pixel_aspect_x/pixel_aspect_y/resolution_x/resolution_y from the renderer is now in Camera
- fixed a bug when the unknown texture folder in the scenenet dataset was not created before
- improved the loading of camera parameters from files
- added a feature for supporting changes of the "category_id" for the WorldManipulator
- improved the visHdf5/saveHdf5/generate_nice_vis scripts
- switches to blender 2.83.2

## Version 1.4.1: 3rd June 2020

- switches to blender 2.83
- adds support for adaptive sampling (Renderer/use_adaptive_sampling) -> can decrease rendering time for complex scenes if used
- add random_samples option for entity getter
- add friction/damping for physics positioning
- add JPG save option for RgbRenderer
- add uniform elevation sampling in Shell Sampler
- add in plane rotation option for look_at/direction camera rotations
- add postprocessing.Dist2Depth to convert Blender distance images to depth images 
- UpperRegionSamlper can sample in relative area on selected face
- improve physics by using convex hull and box collision shapes
- obj.rigid_body.use_margin = True, to actually use margin
- add a Smooth Shader cf to entityManipulator
- BopWriter improvements, outputs chunks of 1000 images
- exclude objects like planes from proximity checks
- fix transparency bounces
- add custom property cp_bop_dataset_name
- add bop_challenge example with all configs used to render the provided synthetic data 
- add bop_object_on_surface_sampling for sampling upright objects
- docu improvements and step by step explanations of config files

## Version 1.4.0: 15th May 2020

- added the NormalRenderer functions to the RGBRenderer saves a render call, when generating normal images
- added a script to automatically download all PBR assest from [https://cc0textures.com/](https://cc0textures.com/)
- add CCMaterialLoader, which can load all downloaded materials from cc0textures, to randomly replace them later
- add support for ShapeNet
- add support for SceneNet, including the lighting, which is modeled after the SUNCG lighting module.
- massive docu improvements, added a type to all config values and a default value if one is there
- added examples for: 
  - bop_object_physics_positioning
  - bop_object_pose_sampling
  - bop_scene_replication
  - on_surface_object_sampling
  - scenenet
  - scenenet_with_cctextures
  - shapenet
  - shapenet_with_scenenet
  - shapenet_with_suncg
  - suncg_with_improved_mat
- added object OnSurfaceSampler (similiar to the phyiscs but faster and places object only on the bb)
- added WorldManipulator (can change custom properties of the world, like the category_id)
- switched to config version 3.0 
  - global initialized values are now in the main.Initializer
  - added a GlobalStorage to save variables over module boundaries
- add VisNormalImage for debugging mode, which visualizes a depth & normal image in blender 
- material selectors now also support AND and OR conditions
- add automatic detection of optix graphics cards
- added a min interest score for the CameraSampler
- added a novelty pose checker for the CameraSampler, to avoid clustering of camera poses
- global config values are now not longer added to the modules config, only in the event that there is no module found the global config is checked
- rename SUNCG materials to the textures they load, makes selecting them easier
- SUNCG materials are now shared over objects, if they share the same properties, also true for lights
- rewrite of MaterialRandomizer to make use of the new cc0textures
- added a Bop Writer to write out the current scene config in the BOP format
- add the solidify modifier to the options of the EntityManipulator
- add a PartSphere sampler to e.g. only sample in the upper half of a sphere
- add a script to download scenenet to make the use of it even easier
- add easy option to change specular values for materials with the MaterialManipulator
- added the option to make runs deterministic by introducing a env variable: `BLENDER_PROC_RANDOM_SEED`
- added a Basic Color Sampler
- improved the capabilities of the DiscSampler
- now all custom properties should be accessed in the config via: "cp_..." for custom functions: "cf_"
- add texture support for ycbv objects in the BopLoader
- change the default results of the SegMapRenderer to NYU ids instead of the row-index in the .csv file.

## Version 1.3.0: 25th March 2020
- added Optical Flow Renderer 
- added Stereo Global Matching Renderer (SGM) -> which takes two color images and produces "non-perfect" depth images
- added option for SGM to also write disparities
- added a new material manipulator 
- added a material getter to select materials based on certain conditions
- combined BOP with this repo -> now the only difference is the readme
- added contribution guidelines -> which include commit message guidelines and branch name guidelines and much more
- matrices can now be read via the config file
- added a cached options to the import objects
- added request custom property for the entity getter (to ensure that a custom property is changed)
- added ReplaceObject
- added option that in debugging the RgbRenderer get executed except for the actual rendering part all others are executed and then undon
- added collision mesh source to the physics module
- added option to coco annotations to append the output to an existing coco file
- added bounding box selection to getter.Entity and also just axis aligned hyper plane checks
- added a 1D sampler for float/int/bool
- added postprocessing to the example to reduce the amount of channels in the depth image
- added visualization for stereo and optical flow
- added an oil filter for the SGM result
- added a path sampler
- added a blender collection loader
- added the RockEssentialLoader based on the RockEssential dataset
- added index to getter.Entity to request only a certain element of the selection
- fix three bugs in the physics module, where the mass_scaling was always used and the location not properly updated
- fixed a bug where color images where wrongly saved in float now back to uint8
- fixed a bug in the coco annotations writer + adapting of the example
- fixed bug in load_image, where the dimensions where switched
- fixed a bug when "home_local" is not available than "home" is used
- fixed bug where run.py can only be run from the main folder
- fixed pypng version in bop example
- fixed bug where the volume calculation for bounding boxes did not work as expected
- refactored the disc sampler 
- cleaned up all readmes


## Version 1.2.0: 31th January 2020

- added more detailed examples to most of the important modules
- adapt CoCo annotation tools to newer Version of SegMapRenderer
- background class is now zero when doing instance segmentation
- renamed getter.Object to getter.Entity, same for ObjectManipulator is now named EntityManipulator
- entity conditions do now work with AND and OR connections
- strings are now matched with fullmatch instead of search in entity conditions
- conditions now support bool custom properties
- material randomizer now supports getter.entity providers
- added UpperRegionSampler, which can sample on the up surface of the bounding box of an object
- scripts now support execution with python3.x
- physics are now saved with bool instead of active and passive
- physics options for simulator added
- remove version number -> only blender version 2.81 supported
- the ObjectLoader can now load several objects at once and set their properties with `"add_properties"`
- moved more functionality in the camera sampler instead of having in specific sampler to make writing a new one easier
- added a SO3 Sampler for rotation sampling
- change the "name" of modules in the config to "module" and "provider" depending on the case
- added MacOS support (but only for CPUs, GPU support on MacOS is not available)
- added this changelog
- fixes:
  - fixed a problem that the check_bb_intersection did not work right in all cases (Bounding box check)
  - fixed a problem with the check_intersection fct., where the reference coordinate system was not always right.
  - fixed a bug with the SUNCG lighting in RGB images

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
