# Benchmark for 6D Object Pose Estimation (BOP)

We provide two example configs that show how to work with the BOP datasets. 

- ```config_replicate.yaml``` replicates whole scenes from BOP
- ```config_sample.yaml``` loads BOP objects and samples object poses and cameras

Note: You can adjust the samples of the renderer to trade-off quality and render time.

## BOP Scene Recreation (```config_replicate.yaml```)

Execute in the Blender-Pipeline main directory:

```
python run.py examples/bop/config_replicate.yaml /path/to/bop/dataset /path/to/output_dir
```

View the generated data and labels using

```
python scripts/visHdf5Files.py /path/to/output_dir/0.hdf5
```
## Steps

* Loads BOP scene with object models, object poses, camera poses and camera intrinsics
* Creates a point light sampled inside a shell
* Renders rgb
* Renders instance segmentation masks
* Writes labels and images to compressed hdf5 files in output_dir

<img src=icbin.png width="240" height="180"> <img src=tless.png width="240" height="180"> <img src=hb.png width="240" height="180"> 


## Sampling BOP objects, cameras and lights (```config_sample.yaml```)

We load BOP objects and alternatingly sample camera poses (looking towards the objects) and object poses (including collision checks). Labels are saved in hdf5 files as well as in the popular COCO format for instance segmentation / detection.

To run the pipeline, simply call:

```
python run.py examples/bop/config_sample.yaml /path/to/bop/dataset /path/to/output_dir
```

Again, view the generated data and labels using

```
python scripts/visHdf5Files.py /path/to/output_dir/0.hdf5
```

Alternatively, since we generated COCO annotations, you can also visualize the generated coco_annotations.json file:
```
python scripts/vis_coco_annotation.py /path/to/output_dir
``` 

## Steps

* Loads object models and camera intrinsics from specified BOP dataset
* Creates a point light sampled inside a shell
* Loops over
    * Sample Object Poses inside a cube with collision checks
    * Sample Camera Poses inside a shell looking at objects
    * Renders rgb
    * Renders instance segmentation masks
    * Writes labels and images to compressed hdf5 files in output_dir

<img src=tless_sample.png width="240" height="180"> <img src=hb_sample.png width="240" height="180"> <img src=hb_sample_inst.png width="240" height="180">

## Explanation of the config file

Here we only discuss loader.BopLoader. The other modules are explained in the [basic](../basic/README.md) and other examples.

#### BopLoader

If `scene_id` is specified, BopLoader recreates the specified scene of the BOP dataset specified by `bop_dataset_path`. All camera poses and intrinsics from the specified scene are also loaded. Be careful to choose a `split` that is actually present in the given BOP dataset and that has ground truth.

```yaml
    {
      "name": "loader.BopLoader",
      "config": {
        "bop_dataset_path": "<args:0>",
        "mm2m": True,
        "split": "val",
        "scene_id": 3,
        "model_type": ""
      }
    },
```

If `scene_id` is not specified, you just load a number of `obj_ids` from the BOP dataset specified by `bop_dataset_path`. 
```yaml
    {
      "name": "loader.BopLoader",
      "config": {
        "bop_dataset_path": "<args:0>",
        "mm2m": True,
        "split": "val",
        "obj_ids": [3,4,4,8],
        "model_type": ""
      }
    },
```

Following modules handle the rest. `composite.CameraObjectSampler` alternates between sampling new cameras using `camera.CameraSampler` and sampling new object poses using `object.ObjectPoseSampler`. Additionally, here you set the parameters

- `noof_cams_per_scene` after which the object poses are resampled
- `total_noof_cams` to generate