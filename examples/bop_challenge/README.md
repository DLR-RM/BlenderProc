# BOP Challenge 2020 Data Generation

<p align="center">
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_tless_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_03.jpg" alt="Front readme image" width=250>
</p>

Here you find the official BlenderProc configs that we used to generate the provided synthetic data for the BOP Challenge 2020 (7 core datasets). The output will be a dataset in [BOP Format](https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md) saved in chunks of 1000 images. 

For LineMOD, the objects are placed upright on a plane based on the [bop_object_on_surface_sampling](../bop_object_on_surface_sampling) example. All other datasets are created by dropping objects using physics based on the [bop_object_physics_positioning](../bop_object_physics_positioning) example. Make sure to read through them if you want to understand and adapt the configs. 

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






