# Planned Features

- Add support for more object datasets (ideas are welcomed, just open an issue with a dataset you want to see integrated)
- Support non-rigid physics simulation
- Improve performance
- Deprecate Global Storage

# Version History

## Version 2.7.1 16th April 2024

- new camera projection helper methods are available: `bproc.camera.depth_via_raytracing()`, `bproc.camera.pointcloud_from_depth()`, `bproc.camera.project_points()`, `bproc.camera.unproject_points()` (#1045, #1075)
- .blend loader now also supports hair_curves (#1052, thanks @sagoyal2)
- adds .usd loader (#1043, thanks @freLorbeer)
- fixes memory leak in bop writer (#1086, thanks @matteomastrogiuseppe)
- fixes removal of scene properties (#1055)
- fixes incorrect warnings regarding hidden objects in bop writer (@1058, thanks @saprrow)
- fixes linking objects when duplicating object hierarchy (@1081, thanks @AndreyYashkin)


## Version 2.7.0 26th January 2024

- upgrades to blender 3.5.1 (#788)
- adds helper methods for easy 3D-2D projection/unprojection, including `bproc.camera.depth_via_raytracing()`, `bproc.camera.pointcloud_from_depth()`, `bproc.camera.project_points()`, `bproc.camera.unproject_points()`, see also [point_cloud](https://github.com/DLR-RM/BlenderProc/tree/main/examples/advanced/point_clouds) example (#1045)
- removes support for obsolete .yaml configuration files (#962)
- speeds up bop writer for large number of objects - for 300 objects, the bop writer execution time reduces from 60s to 12s with 8 cores (#996)
- adds warning if hidden objects are given to bop writer (#998)
- skip transparent cc materials per default (#1004)
- rework of `duplicate()`: allows linking and keeps parent relative transformation matrix (#1012, thanks @AndreyYashkin)
- moves `hide()` and `is_hidden()` to Entity class (#1015, thanks @AndreyYashkin)
- fixes optical flow output key being overwritten by RGB (#963)
- fixes `--custom-blender-path` on windows (#972)
- adapts downloading cc_textures to new naming scheme (#976, #993)
- fixes issue in light projector (#995, thanks @beekama)
- fixes skipping annotation indices when appending coco annotations (#1024)
- fixes frame offset in rendering progress bar (#1038, thanks @burcam)

## Version 2.6.2 6th December 2023

- Fixes blender download 

## Version 2.6.1 26th August 2023

- Fixes pyrender usage on windows, EGL / headless rendering is now only used on linux

## Version 2.6.0 17th August 2023

- BOP toolkit is now tightly integrated into the the BOP writer:
  - Ground truth masks and coco annotations are now directly calculated when calling the BOP writer
  - Instead of using vispy for renderings the masks, we switched to pyrender which speeds up the process a lot
- rendering/physics log is now hidded per default and instead a pretty progress bar is shown
- upgrades to blender 3.3.1
- its now possible to render segmentation images in stereo mode
- adds method to MeshObject to convert to trimesh
- fixes rendering on cpu-only (thanks @muedavid)
- adds support for loading .glb/.gltf meshes (thanks @woodbridge)
- adds support for loading .fbx meshes (thanks @HectorAnadon)
- allows setting rotation for hdri backgrounds (thanks @saprrow)
- incorporate location changes to urdf local2world matrix calculations
- allows setting brightness for hdri backgrounds 
- `bproc.object.sample_poses_on_surface()` now hides objects which could not be placed instead of deleting them
- removes duplicate categories and fixes segmentation id when writing scene_gt.json annotations in BOP writer (thanks @hansaskov)
- `get_all_cps()` now returns a proper dictionary (thanks @andrewyguo)
- replaces deprecated `np.bool` with bool (thanks @NnamdiN)
- refactoring of haven download script to support multithreading (thanks @hansaskov)
- fixes loading stl files in urdf files
- loading a .ply objects automatically sets the materials to its vertex color if no texture file was found.
- username is now retrieved in a more platform independent way (thanks @YouJiacheng)
- coco annotations are now nicely formatted (thanks @andrewyguo)
- object pose sampler now correctly sets rotation if mode on failer was set to `initial_pose`


## Version 2.5.0 20th September 2022
- segmentations are now done in the same call as any other render call, avoiding the loading of the objects for each pose
- added the kinect azure noise model, allowing for the creation of more realistic depth images
- added a spotlight intersection mode, which places a spotlight in the world without intersecting with the current camera frustum, while it focuses on the middle of the camera frustum, creating hard lighting situations
- add an importer for the MatterPort3d dataset
- the key of custom properties now can no longer have the same name as any attribute of the `blender_obj`. Custom properties do not need to start with `cp_` anymore
- add a new paper designated for the journal of sensors
- we now use pylint to clean up all code smells and add documentation to all functions
- the bop loader now also supports the hope dataset
- separate the init and clean up functions
- it can now be specified which GPU to use for rendering, if multiple are available
- rewrite the ambient CG download script, allowing resuming the download
- turn of the cycle denoiser causing issues in certain settings
- add a random walk feature, which allows simulating a camera shaking or POI drift
- the duplicate and delete fcts now support duplicating all children as well, we added a `get_children` fct as well
- renaming `get_rotation` to `get_rotation_euler` and adding functions for setting the rotation matrix
- fix a bug in the move_origin_to_bottom_mean fct.

## Version 2.4.1 22th July 2022
- allow writing poses for robot links in the BopWriter
- loading .obj files now uses the faster importer
- fix a pip install bug
- fix a bug in the LinkUtility of the URDF loader

## Version 2.4.0 20th July 2022
- add urdf support: 
  - this enables the simulation of robotic arms with forward and inverse kinematics
  - add an example to show of how this works
- add a new face slicer option, making it easier to slice the top of a table away for placing objects on them
- add a new example for sampling objects in 3D Front scenes
- switch to vhacd version 4.X allowing for faster decompositions than before, speeding up the simulation
- add an option to link blend files instead of loading them (faster, but objects can not be changed after linking)
- add a new replica loader, loading semantic objects instead of just one mesh for the whole scene
- add basic support for apple silicion (M1, M2), this might still mean that some packages have to be installed on their own afterwards
- add return random material to the load haven material function, the function returns also now the full loaded list of materials
- add new function to create a material based soley on a texture (Path or bpy.types.Image)
- upgrade to blender 3.2.1 
- reduce the memory demand of the semantic segmentation by fixing a small bug
- fix a bug where the coco annotation writer wouldn't work if the frame_start is not zero
- fix a bug where writing alpha images in the bop writer did not work
- fix a bug where pip would reinstall packages all the time
- fix a bug where on windows the pip path would be wrong

## Version 2.3.0 22th March 2022
- upgrade to blender 3.1.0 
  - add support for Apple Silicon and GPU on Mac OS 12.3 
- add new stereo image projector, making it easier to simulate SGM depth
- add quickstart command `blenderproc quickstart`
- add gif writer 
- function to scale the UV texture coordinates of a `MeshObject`
- `object.sample_poses()` now also supports a `mode_on_failure`, which allows to control where the object is placed if the sampling fails @marcelhohn 
- improve error message for python 2.X
- bug fixes:
  - `set_origin()` doesn't change the cursor position anymore @marcelhohn
  - `vis hdf5 --save` now also supports stereo images
  - improve error message when rendering with no camera poses
  - fixed a bug where the windows path was incorrect for blender @marcelhohn
  - fixed a bug when the category name is an int during coco vis
  - `load_haven_mat()` now loads more materials, not all materials have been used before @Victorlouisdg

## Version 2.2.0 17th December 2021
- switch blender version to 3.0.0 instead of 2.93.0 
  - we now rely on Cycles X, making the rendering much faster than before
  - this also depreactes the usage of `bproc.renderer.set_samples()`, this is now replaced with `bproc.renderer.set_noise_threshold()`. This fcts allows to set the desired noise ration on a pixel basis, giving a much higher control to ensure a certain consistent noise level in the whole image. 
  - it is still possible to limit the amount of samples per pixel with a new function named: `bproc.renderer.set_max_amount_of_samples()`
  - as the whole image is now rendered at once we removed the auto-tile addon
  - the BLENDER denoiser is no longer available, we recommend using the INTEL denoiser.
- remove the argument `keep_using_base_color` from `bproc.lighting.light_surface()` and `Material.make_emissive()`, now either a emission color or the base color is used
- changes for the bop integration
  - install bop_toolkit automatically
  - add BlenderProc2 python scripts for BOP challenge
  - allow to pass list of objects to `write_bop` for which to save pose annotations
  - divide `load_bop()` into `load_bop_objs()`, `load_bop_scene()` and `load_bop_intrinsics()` to decouple the functionalit
- fix a bug after uninstalling pip packages they were not truly removed

## Version 2.1.0 17th November 2021
- add new lens distortion module, adding the possibility to simulate `k1, k2, k3, p1` and `p2` parameters. 
- improve usability of distance rendering, make it the default in all examples
- distance and depth rendering can now be done antialiased and non-antialiased
- add a nocs renderer: [paper](https://geometry.stanford.edu/projects/NOCS_CVPR2019/pub/NOCS_CVPR2019.pdf)
- upgrade the shell sampler and rework the usage and documentation
- move `run.py` to `cli.py` and support the same CLI arguments as for `blenderproc ...`
- make caching of pip installs the default (faster start-up) and add option to reset them if needed
- refactor the vishdf5 script using the same content now for saveAsImg
- clean up the scripts folder and move it completely into blenderproc
- include all packages (like vhacd) in the pip install package
- fix bug with light internal blender_obj after an undo operation
- add OPTIX as denoiser option
- add possibility to read `jpeg` 
- fix `use_ray_trace` in `bproc.sampler.upper_region`
- added an exception if not the correct python environment is used

## Version 2.0.0a7 13th October 2021
- fix `Light` class to work properly with `bpy.types.Light` in `load_blend`
- fix the stereo matching example add missing parameter to fct. call

## Version 2.0.0a6 13th October 2021
- moved to a full python API support (`.yaml` files are still supported)
  - blenderproc can now be installed via pip: `pip install blenderproc` 
  - complete new structure to most of the files
  - offer new command line interfaces: `blenderproc run`, `blenderproc debug`, `blenderproc vis` and many more 
  - optional/flag arguments can now be used in the users python script
- adds feature to render multiple times in one session (see example `advanced/multi_render`)
- added tutorials to get easy start with BlenderProc
- adjusted all examples to explain how the python API would be used there
- restructured the documentation
- fixed a bug with the view layer update, which wasn't done before the scene coverage score was calculated, which caused problems in the 3D-FRONT examples.
- removed a lot of view layer update calls, which makes the whole execution faster, by manually calculation the `matrix_world`.
- vertex colors can now be used with a Principled BSDF shader
- all images are now moved into a seperate `image/` directory
- all functions now use type hints

## Version 1.12.0 23th July 2021
- switch to blender 2.93, with that textures are now stored on the GPU between different frames increasing the speed drastically
- moved a lot of modules to the python API
  - all camera samplers
  - all writer classes
  - sampler and getters
  - surface lighting
  - random room constructor
- all outer API functions work now with numpy arrays instead of mathutils classes
- regroup all examples to make them more easily accessible
- refactoring of the LabelIdMapping class
- sampler.Path now has a `return_all` and `random_samples` option
- add support for the new 3D front labels and script to find them more easily in the future
- AMASS now also supports `torch=1.8.1+cu111`, to better support modern GPUs
- refactor download script for haven
- added a flag to not center objects from the ShapeNet dataset
- added a platform independent unzipping function to solve the problems on windows
- add function to return the default_value or the connected node based on the input name of a BSDF shader node of a material
- fix for MacOS, where the blender version was not used in prior installations, leading to the problem that users had to remove blender on their own
- the writer now correctly writes the fov if asked

## Version 1.11.1 18th May 2021
- fix a bug on mac os, where the blender python path has changed
- fix a bug in the BlenderLoaderModule which caused that the setting of custom properties was not successful

## Version 1.11.0 11th May 2021
- BlenderProc now can be executed via a python script (experimental, not all modules are supported yet)
- python API extension for the following modules:
  - the Entity & Material Manipulation
  - the WriterUtility, Hdf5Writer, BopWriterUtility, CocoWriterUtility
  - the PostProcessing
  - the physic positioning, PoseSampler
- debugging can now be done via the command line, by just typing --debug after a BlenderProc call
- add automatic convex decomposition to speed up physics, object decompositions will be cached
- add a jupyter notebook example for google colab
- add a BasicEmptyInitializer module, which helps creating simple empty objects, these can be used for using a depth of field
- add a depth_of_field option to the CameraInterface (thanks to cuteday)
- add a hide module, so that certain objects can be hidden in a selected range of frames (thanks to Sainan Liu)
- add an option to change the computation type via the config
- blender 2.92 changed depth and distance once again, we use it correctly now and added an explanation
- added a diffuse rendering mode
- added a key frame API
- added a default config, which can be easily changed
- ObjectPoseSampler now can check also against only a limited set of objects
- ObjectReplacer now stops if no objects are left to replace
- SurfaceLighting now reuses the TextureLess material
- preloading in CCTexture now also works perfectly for textures which use an alpha texture
- python packages now are installed by specifying the required packages at the top of each file
- added an example for pasting objects onto random backgrounds
- added a flag to merge BlenderKit objects, while loading, they will be named after the blenderkit file
- reintroduce persistent transformation scaling to improve stability
- improve the clean up at the start of BlenderProc
- fixed a bug in the Front3DLoader, which avoided the correct setting of the custom properties
- fixed a bug with the once_for_all mode for the randomize materials fct.
- add a simple rerun script to show how BlenderProc is used for creating a diverse dataset
- switch to blender 2.92

## Version 1.10.0 24th February 2021
- rewritten the `BlendLoader`, which is now able to only load objects of a given type, this will break existing config files as the `load_from` parameter has been replaced by `datablocks` and `obj_types`
- the `MaterialManipulator` can now overlay/mix a texture with a selected material
- the `MaterialManipulator` can now mix/add a material with another selected material, ideal for creating surface imperfections on other materials
- the `MaterialManipulator` can now add a layer of dust on materials, which simulates dust flakes on top of the object, there also exists now an example for it
- `amount_of_repetitions` can now be used with providers  
- full integration of the blenderkit module, including modules and textures with an example
- `LoaderInterface` now offers an auto shading mode
- the `CCMaterialLoader` uses now a preselected list of probably useful materials by default to avoid non tileable materials
- restructure loaders and move their functionality to the utilities (necessary for the API changes for 2.0.0)

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
