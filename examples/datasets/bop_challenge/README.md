# BOP Challenge 2020 Data Generation

<p align="center">
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_tless_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_01.jpg" alt="Front readme image" width=250>
<img src="https://bop.felk.cvut.cz/static/img/bop20_pbr/bop20_pbr_ycbv_03.jpg" alt="Front readme image" width=250>
</p>

Here you find the official BlenderProc implementations that we used to generate the [provided synthetic data](https://bop.felk.cvut.cz/datasets/) for the BOP Challenge (7 core datasets). The output datasets are saved in [BOP Format](https://github.com/thodan/bop_toolkit/blob/master/docs/bop_datasets_format.md) in chunks of 1000 images. 

The prerendered datasets with 50K images each are available [here](https://bop.felk.cvut.cz/datasets/), where they are called "PBR-BlenderProc4BOP training images". 

For LineMOD, the objects are placed upright on a plane based on the [bop_object_on_surface_sampling](../bop_object_on_surface_sampling/README.md) example. All other datasets are created by dropping objects using physics based on the [bop_object_physics_positioning](../bop_object_physics_positioning/README.md) example. 

## Instructions to generate the data

Here, we explain the usage with the new python format introduced in BlenderProc2, for the original config files, check [below](#original-config-file-usage).

Download the necessary [BOP datasets](https://bop.felk.cvut.cz/datasets/). Base archives and 3D models are sufficient.

Execute in the BlenderProc main directory:

```
blenderproc download cc_textures 
```

The following command creates 50K training images in BOP format for the given dataset 
```
blenderpoc run examples/datasets/bop_challenge/main_<bop_dataset_name>_<random/upright>.py 
               <path_to_bop_data> 
               resources/cctextures 
               examples/datasets/bop_challenge/output
               --num_scenes=2000
``` 

* `examples/datasets/bop_challenge/main_<bop_dataset_name>_<random/upright>.py`: path to the python file.
* `<path_to_bop_data>`: path to a folder containing BOP datasets.
* `resources/cctextures`: path to CCTextures folder
* `examples/datasets/bop_challenge/output`: path to an output folder where the bop_data will be saved
* `--num_scenes`: How many scenes with 25 images each to generate

Tip: If you have access to multiple GPUs, you can speedup the process by dividing the 2000 scenes into multiples of 40 scenes (40 scenes * 25 images make up one chunk of 1000 images). Therefore run the script in parallel with different output folders. At the end, rename and merge the scenes in a joint folder. For example, if you have 10 GPUs, set `--num_scenes=200` and run the script 10 times with different output folders.
