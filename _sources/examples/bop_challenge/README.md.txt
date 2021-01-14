# BOP Challenge 2020 Data Generation

<p align="center">
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_tless_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_03.jpg" alt="Front readme image" width=250>
</p>

Here you find the official BlenderProc configs that we used to generate the [provided synthetic data](https://bop.felk.cvut.cz/datasets/) for the BOP Challenge 2020 (7 core datasets). The output datasets are saved in [BOP Format](https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md) in chunks of 1000 images. 

The prerendered datasets with 50K images each are available [here](https://bop.felk.cvut.cz/datasets/), where they are called "PBR-BlenderProc4BOP training images". We ran every config file 2000 times with 25 random cameras per scene. 

For LineMOD, the objects are placed upright on a plane based on the [bop_object_on_surface_sampling](../bop_object_on_surface_sampling/README.md) example. All other datasets are created by dropping objects using physics based on the [bop_object_physics_positioning](../bop_object_physics_positioning/README.md) example. Make sure to read through them if you want to understand and adapt the configs. 

## Usage

Download the necessary [BOP datasets](https://bop.felk.cvut.cz/datasets/) and the [bop-toolkit](https://github.com/thodan/bop_toolkit). 

Execute in the BlenderProc main directory:

```
python scripts/download_cc_textures.py 
```

```
python run.py examples/bop_challenge/<config_dataset.yaml> 
              <path_to_bop_data> 
              <bop_dataset_name> 
              <path_to_bop_toolkit> 
              resources/cctextures 
              examples/bop_challenge/output
``` 

* `examples/bop_challenge/<config_dataset.yaml>`: path to the pipeline configuration file.
* `<path_to_bop_data>`: path to a folder containing BOP datasets.
* `<bop_dataset_name>`: name of BOP dataset.
* `<path_to_bop_toolkit>`: path to a bop_toolkit folder.
* `resources/cctextures`: path to CCTextures folder
* `examples/bop_challenge/output`: path to an output folder where the bop_data will be saved

This creates 25 images of a single scene. To create a whole dataset, simply run the command multiple times.

### Note

To save some time and not copy functionality we use the bop_toolkit to generate the [masks](
https://github.com/thodan/bop_toolkit/blob/master/scripts/calc_gt_masks.py) and also the [scene_gt_info](https://github.com/thodan/bop_toolkit/blob/master/scripts/calc_gt_info.py). There, you will also find a Bop2coco annotations converter.

Don't forget to set the paths to your generated BOP dataset in bop_toolkit_lib/config.py.
