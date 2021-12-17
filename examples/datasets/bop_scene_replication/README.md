## Benchmark for 6D Object Pose Estimation (BOP) <br/> Scene Replication

<img src=../../../images/bop_scene_replication_hb.jpg width="240" height="180"> <img src=../../../images/bop_scene_replication_icbin.jpg width="240" height="180"> <img src=../../../images/bop_scene_replication_tless.jpg width="240" height="180">

This example shows how to synthetically recreate BOP scenes.

## Usage

First make sure that you have downloaded a [BOP dataset](https://bop.felk.cvut.cz/datasets/) in the original folder structure.

In [examples/datasets/bop_scene_replication/main.py](main.py) set the `blender_install_path` where Blender is or should be installed.

Execute in the BlenderProc main directory: 

```
blenderproc run examples/datasets/bop_scene_replication/main.py <path_to_bop_data> <bop_dataset_name> examples/datasets/bop_scene_replication/output
```
* `examples/datasets/bop_scene_replication/main.py`: path to the python file with pipeline configuration.
* `<path_to_bop_data>`: path to a folder containing BOP datasets.
* `<bop_dataset_name>`: name of BOP dataset, e.g. tless
* `examples/datasets/bop_scene_replication/output`: path to the output directory.

## Visualization

Visualize the generated data and labels:

```
blenderproc vis hdf5 example/bop_scene_replication/0.hdf5
```

## Steps

* Loads BOP scene with object models, object poses, camera poses and camera intrinsics: `bproc.loader.load_bop_scene()`.
* Creates a point light sampled inside a shell.
* Renders rgb: `bproc.renderer()`.
* Renders instance segmentation masks: `bproc.renderer()`.
* Writes pose labels in BOP format to output_dir: `bproc.writer.write_bop()`.

## Python file (main.py)

### BopLoader

```python
bop_objs = bproc.loader.load_bop_scene(bop_dataset_path = os.path.join(args.bop_parent_path, args.bop_dataset_name),
                          mm2m = True,
                          scene_id = 1,
                          split = 'test') # careful, some BOP datasets only have labeled 'val' sets

```

If `scene_id` is specified, BopLoader recreates the specified scene of the BOP dataset specified by `bop_dataset_path`. All camera poses and intrinsics from the specified scene are also loaded.  
Be careful to choose a `split` that is actually present in the given BOP dataset and that has ground truth.  
For some BOP datasets you can choose the `model_type`, e.g. `reconst` or `cad` in T-LESS. 

## More examples

* [bop_object_pose_sampling](../bop_object_pose_sampling/README.md): More on sampling objects, cameras and lights.
* [bop_object_physics_positioning](../bop_object_physics_positioning/README.md): Drop BOP objects on planes and randomize materials
