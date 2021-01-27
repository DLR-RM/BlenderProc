## Benchmark for 6D Object Pose Estimation (BOP) <br/> Scene Replication

<img src=hb.png width="240" height="180"> <img src=icbin.png width="240" height="180"> <img src=tless.png width="240" height="180">

This example shows how to synthetically recreate BOP scenes.

## Usage

First make sure that you have downloaded a [BOP dataset](https://bop.felk.cvut.cz/datasets/) in the original folder structure. Also please clone the [BOP toolkit](https://github.com/thodan/bop_toolkit).

In [examples/bop_scene_replication/config.yaml](config.yaml) set the `blender_install_path` where Blender is or should be installed.

Execute in the BlenderProc main directory: 

```
python run.py examples/bop_scene_replication/config.yaml <path_to_bop_data> <bop_dataset_name> <path_to_bop_toolkit> examples/bop_scene_replication/output
```
* `examples/bop_scene_replication/config.yaml`: path to the pipeline configuration file.
* `<path_to_bop_data>`: path to a folder containing BOP datasets.
* `<bop_dataset_name>`: name of BOP dataset, e.g. tless
* `<path_to_bop_toolkit> `: path to the BOP toolkit containing dataset parameters, etc.
* `examples/bop_scene_replication/output`: path to the output directory.

## Visualization

Visualize the generated data and labels:

```
python scripts/visHdf5Files.py example/bop_scene_replication/0.hdf5
```

## Steps

* Loads BOP scene with object models, object poses, camera poses and camera intrinsics: `loader.BopLoader` module.
* Creates a point light sampled inside a shell: `lighting.LightSampler` module.
* Renders rgb: `renderer.RgbRenderer` module.
* Renders instance segmentation masks: `renderer.SegMapRenderer` module.
* Writes labels and images to compressed hdf5 files in output_dir: `writer.Hdf5Writer` module.
* Writes pose labels in BOP format to output_dir: `writer.BopWriter` module.

## Config file

### BopLoader

```yaml
    {
      "module": "loader.BopLoader",
      "config": {
        "source_frame": ["X", "-Y", "-Z"],
        "bop_dataset_path": "<args:0>/<args:1>",
        "mm2m": True,
        "split": "test", # careful, some BOP datasets only have test sets
        "scene_id": 1,
        "model_type": ""
      }
    }
```

If `scene_id` is specified, BopLoader recreates the specified scene of the BOP dataset specified by `bop_dataset_path`. All camera poses and intrinsics from the specified scene are also loaded.  
Be careful to choose a `split` that is actually present in the given BOP dataset and that has ground truth.  
For some BOP datasets you can choose the `model_type`, e.g. `reconst` or `cad` in T-LESS. 

## More examples

* [bop_object_pose_sampling](../bop_object_pose_sampling/README.md): More on sampling objects, cameras and lights.
* [bop_object_physics_positioning](../bop_object_physics_positioning/README.md): Drop BOP objects on planes and randomize materials
