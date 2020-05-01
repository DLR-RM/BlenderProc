# Name of the example

TODO

This example presents some advanced BlenderProc features used for BOP data integration, namely object sampling, material manipulation and randomization, etc.

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py examples/bop_with_object_sampling/config.yaml <path_to_bop_data> <path_to_bop_toolkit> examples/bop_with_object_sampling/output
``` 

* `examples/bop_with_object_sampling/config.yaml`: path to the pipeline configuration file.
* `<path_to_bop_data>`: path to a folder containing BOP datasets.
* `<path_to_bop_toolkit>`: path to a bop_toolkit folder.
* `examples/bop_with_object_sampling/output`: path to an outputfolder.

## Visualization

Visualize the generated data if it is stored in a container.

```
python scripts/visHdf5Files.py examples/bop_with_object_sampling/output/coco_data/0.hdf5
```

## Steps

TODO

## Config file

### Some module

```yaml
    "the config": "section relevant"
    "for the module": "you are explaining"
```

TODO

### Some other module

...


## More examples

* [bop_sampling](../bop_sampling): Sample BOP object and camera poses.
* [bop_scene_replication](../bop_scene_replication): Replicate the scenes and cameras from BOP datasets in simulation.
