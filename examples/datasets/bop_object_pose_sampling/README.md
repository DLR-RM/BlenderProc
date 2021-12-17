## Benchmark for 6D Object Pose Estimation (BOP) <br/> Sampling objects, cameras and lights

<img src=../../../images/bop_object_pose_sampling_tless_sample.jpg width="240" height="180"> <img src=../../../images/bop_object_pose_sampling_hb_sample.jpg width="240" height="180"> <img src=../../../images/bop_object_pose_sampling_hb_sample_inst.jpg width="240" height="180">

This example shows how to load BOP objects and alternatingly sample light poses, camera poses (looking towards the objects) and object poses (including collision checks).

## Usage

First make sure that you have downloaded a [BOP dataset](https://bop.felk.cvut.cz/datasets/) in the original folder structure.

In [examples/datasets/bop_object_pose_sampling/main.py](main.py) set the `blender_install_path` where Blender is or should be installed.

Execute in the BlenderProc main directory:  

```
blenderproc run examples/datasets/bop_object_pose_sampling/main.py <path_to_bop_data> <bop_dataset_name> examples/datasets/bop_object_pose_sampling/output
```
* `examples/datasets/bop_object_pose_sampling/main.py`: path to the python file with pipeline configuration.
* `<path_to_bop_data>`: path to a folder containing BOP datasets.
* `<bop_dataset_name>`: name of BOP dataset, e.g. lm
* `examples/datasets/bop_object_pose_sampling/output`: path to the output directory.

## Visualization

Visualize the generated data and labels:
```
blenderproc vis hdf5 examples/datasets/bop_object_pose_sampling/output/0.hdf5
```

Alternatively, since we generated COCO annotations, you can also visualize the generated coco_annotations.json file:
```
blenderproc vis coco /path/to/output_dir
``` 

## Steps

* Loads object models and camera intrinsics from specified BOP dataset: `bproc.loader.load_bop_objs()`, `bproc.loader.load_bop_intrinsics()`.
* Creates a point light sampled inside a shell
* Loops over five times:
    * Sample Object Poses inside a cube with collision checks
    * Sample Camera Poses inside a shell looking at objects
* Renders rgb: `bproc.renderer`.
* Renders instance segmentation masks: `bproc.renderer()`.
* Writes pose labels in BOP format to output_dir: `bproc.writer.write_bop()`.

## Python file (main.py)

### BopLoader

`bproc.loader.load_bop_objs()` simply loads all or the specified `obj_ids` from the BOP dataset given by `bop_dataset_path`. 
`bproc.loader.load_bop_intrinsics()` sets the intrinsics of the BOP dataset.

```python
bop_objs = bproc.loader.load_bop_objs(bop_dataset_path = os.path.join(args.bop_parent_path, args.bop_dataset_name),
                          mm2m = True,
                          obj_ids = [1, 1, 3])

bproc.loader.load_bop_intrinsics(bop_dataset_path = os.path.join(args.bop_parent_path, args.bop_dataset_name))  
```

### CameraObjectSampler

```python
# Sample object poses and check collisions 
    bproc.object.sample_poses(objects_to_sample = bop_objs,
                            sample_pose_func = sample_pose_func, 
                            max_tries = 1000)

    # BVH tree used for camera obstacle checks
    bop_bvh_tree = bproc.object.create_bvh_tree_multi_objects(bop_objs)
    poses = 0
    # Render two camera poses
    while poses < 2:
        # Sample location
        location = bproc.sampler.shell(center = [0, 0, 0],
                                radius_min = 1,
                                radius_max = 1.2,
                                elevation_min = 1,
                                elevation_max = 89,
                                uniform_volume = False)
        # Determine point of interest in scene as the object closest to the mean of a subset of objects
        poi = bproc.object.compute_poi(bop_objs)
        # Compute rotation based on vector going from location towards poi
        rotation_matrix = bproc.camera.rotation_from_forward_vec(poi - location, inplane_rot=np.random.uniform(-0.7854, 0.7854))
        # Add homog cam pose based on location an rotation
        cam2world_matrix = bproc.math.build_transformation_mat(location, rotation_matrix)
        
        # Check that obstacles are at least 0.3 meter away from the camera and make sure the view interesting enough
        if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 0.3}, bop_bvh_tree):
            # Persist camera pose
            bproc.camera.add_camera_pose(cam2world_matrix, 
                                          frame = poses)
            poses += 1
```

This alternates between sampling new cameras using a `bproc.camera` and sampling new object poses using a `bproc.object.sample_poses()`.

### CocoAnnotationsWriter

```python
bproc.writer.write_coco_annotations(os.path.join(args.output_dir, 'coco_data'),
                            supercategory = args.bop_dataset_name,
                            instance_segmaps = seg_data["instance_segmaps"],
                            instance_attribute_maps = seg_data["instance_attribute_maps"],
                            colors = data["colors"],
                            color_file_format = "JPEG", 
                            append_to_existing_output = True)
```
Writes CocoAnnotations of all objects from the given BOP dataset (`"supercategory"`).

### BopWriter

```python
  bproc.writer.write_bop(os.path.join(args.output_dir, 'bop_data'),
                           dataset = args.bop_dataset_name,
                           depths = data["depth"],
                           depth_scale = 1.0, 
                           colors = data["colors"], 
                           color_file_format = "JPEG", 
                           append_to_existing_output = True)
```

Writes object to camera poses and intrinsics of the given `"dataset": "args.bop_dataset_name"` in BOP format. If output folder exists outputs are appended with `"append_to_existing_output": True`.

`"depth_scale": 1.0`: Multiply the uint16 output depth image with this factor to get depth in mm. Used to trade-off between depth accuracy and maximum depth value. Default value `"depth_scale": 1.0` corresponds to 65.54m maximum depth and 1mm accuracy. 

## More examples

* [bop_scene_replication](../bop_scene_replication/README.md): Replicate the scenes and cameras from BOP datasets in simulation.
* [bop_object_physics_positioning](../bop_object_physics_positioning/README.md): Drop BOP objects on planes and randomize materials
* [bop_object_on_surface_sampling](../bop_object_on_surface_sampling/README.md): Sample upright poses on plane and randomize materials
