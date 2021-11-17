# Replica dataset

This example introduces new tools for using replica dataset with BlenderProc.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/datasets/replica/main.py <path_to_the_replica_data_folder>  examples/datasets/replica/output
``` 

* `examples/datasets/replica/main.py`: path to the python file with pipeline configuration.
* `<path_to_the_replica_data_folder>`: Path to the replica dataset directory.
* `examples/datasets/replica/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 example/replica/0.hdf5
```

## Steps

* Load the replica dataset : `bproc.loader.load_replica()`.
* Extract the floor from the room: `bproc.object.extract_floor()`.
* Find point of interest, all cam poses should look towards it: `bproc.object.compute_poi()`.
* Sample random camera location around the objects: `bproc.sampler.sphere()`.
* Adds camera pose to the scene: `bproc.camera.add_camera_pose()`.
* Enables normals and depth (rgb is enabled by default): `bproc.renderer.enable_normals_output()` `bproc.renderer.enable_depth_output()`.
* Renders all set camera poses: `bproc.renderer.render()`.
* Writes the output to .hdf5 containers: `bproc.writer.write_hdf5()`

## Python file (main.py)

### Global

```python
# Load the replica dataset
objs = bproc.loader.load_replica(args.replica_data_folder, data_set_name="office_1", use_smooth_shading=True)
```

Note that `"data_set_name": "office_1"` is a replica room you want to render. This line can be replace with:
`"data_set_name": "<args:X>>"`, i.e. with an appropriate placeholder where `X` is a number of a placeholder.

As before all these values are stored in the GlobalStorage and are only used if no value are defined.

`bproc.loader.load_replica` handles importing objects from a given path. Here we are using smooth shading on all surfaces, instead of flat shading.

### Floor extractor

```python
# Extract the floor from the loaded room
floor = bproc.object.extract_floor(objs, new_name_for_object="floor")[0]
room = bproc.filter.one_by_attr(objs, "name", "mesh")
```

`bproc.object.extract_floor()` searches for the specified object and splits the surfaces which point upwards at a specified level away.

### Replica camera sampler

```python
# Init sampler for sampling locations inside the loaded replica room
point_sampler = bproc.sampler.ReplicaPointInRoomSampler(room, floor, height_list_values)

# define the camera intrinsics
bproc.camera.set_resolution(512, 512)

# Init bvh tree containing all mesh objects
bvh_tree = bproc.object.create_bvh_tree_multi_objects([room, floor])

poses = 0
tries = 0
while tries < 10000 and poses < 15:
    # Sample point inside room at 1.55m height
    location = point_sampler.sample(height=1.55)
    # Sample rotation (fix around X and Y axis)
    rotation = np.random.uniform([1.373401334, 0, 0], [1.373401334, 0, 2 * np.pi])
    cam2world_matrix = bproc.math.build_transformation_mat(location, rotation)

    # Check that obstacles are at least 1 meter away from the camera and have an average distance between 2 and 4 meters
    if bproc.camera.perform_obstacle_in_view_check(cam2world_matrix, {"min": 1.0, "avg": {"min": 2.0, "max": 4.0}}, bvh_tree):
        bproc.camera.add_camera_pose(cam2world_matrix)
        poses += 1
    tries += 1
```

This samples multiple camera poses per every imported room with camera-object collision check and obstacle check.
## Material Manipulator 

```python
# Use vertex color of mesh as texture for all materials
for mat in room.get_materials():
    mat.map_vertex_color("Col", active_shading=False)
```

The `mat.map_vertex_color()` changes the material of the Replica objects so that the vertex color is renderer, this makes it possible to render colors on Replica scenes.
**Important: This does not mean that we load the complex texture files, we only use the low res vertex color for color rendering.**

If you are in need of high-res color images, do we propose that you, yourself can try to implement the texture importer for the replica dataset.
