# 3D Front Dataset

<p align="center">
<img src="rendering_0.png" alt="Front readme image" width=375>
<img src="rendering_1.png" alt="Front readme image" width=375>
</p>

In this example we explain to you how to use the 3D-Front Dataset with the BlenderProc pipeline.
This is an advanced example, make sure that you have executed the basic examples before proceeding to this one.

## Get the 3D-Front dataset

As you are required to agree to the Use Of Terms for this dataset, we can not provide a download script.

However, we will give you a step by step explanation on how to get access.

1. Visit the following webiste and download the "3D-FRONT Terms of Use" as a pdf: `https://tianchi.aliyun.com/specials/promotion/alibaba-3d-scene-dataset`
2. Write an E-Mail to `3dfront@list.alibaba-inc.com` with the content shown below and **attach the Terms of Use pdf**: 
3. They will reply with three links one for the house, which is referred to as the 3D-Front dataset and a link to the furniture, which is called 3D-Future and lastly one for the 3D-Front-textures. Download all of them and save them in a folder.
4. Unzip all files, which should give you three folders one for the houses (3D-FRONT) and one for the furniture (3D-FUTURE-model) and one for the textures. So far we have no use for the `categories.py` and the `model_info.json`.
5. Inside the 3D-FRONT folder you will find the json files, where each file represent its own house/flat. The 3D-FUTURE-model path only has to be passed as second argument, the objects will be automatically selected, same for the 3D-front-texture path.


```text
Dear 3D Future Team,

I hereby agree to the Terms of Use defined in the attached document.

Name: {YOUR NAME}
Affiliation: {YOUR AFFILIATION}

Best regards,
{YOUR NAME}
```

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/datasets/front_3d/config.yaml {PATH_TO_3D-Front-Json-File} {PATH_TO_3D-Future} {PATH_TO_3D-Front-texture} examples/datasets/front_3d/output 
```

* `examples/datasets/front_3d/config.yaml`: path to the configuration file with pipeline configuration.

The three arguments afterwards are used to fill placeholders like `<args:0>` inside this config file.
* `PATH_TO_3D-Front-Json-File`: path to the 3D-Front json file 
* `PATH_TO_3D-Future`: path to the folder where all 3D-Future objects are stored 
* `PATH_TO_3D-Front-texture`: path to the folder where all 3D-Front textures are stored 
* `examples/datasets/front_3d/output`: path to the output directory

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/datasets/front_3d/output/0.hdf5
```

## Steps

* Loads the `.json` file: `loader.Front3DLoader` module. It loads all modules and creates the rooms, it furthermore also adds emission shaders to the ceiling and lamps.
* Sets the category_id of the background to 0: `manipulators.WorldManipulator`
* Adds cameras to the scene: `camera.Front3DCameraSampler`
* Renders rgb, normals: `renderer.RgbRenderer` module.
* Renders semantic segmentation: `renderer.SegMapRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module, removes unnecessary channels for the `"distance"`

## Config file


#### Front3DLoader 

```yaml
{
  "module": "loader.Front3DLoader",
  "config": {
    "json_path": "<args:0>",
    "3D_future_model_path": "<args:1>",
    "3D_front_texture_path": "<args:2>"
  }
}
```

* This module imports an 3D-Front.json file into the scene.
* It also needs the path to the `3D-FUTURE-model` and to the `3D-Front-texture`
* It is also possible to set the strength of the lights here, check the top of the Front3DLoader for more information.

#### Front3DCameraSampler 

```yaml
{
  "module": "camera.Front3DCameraSampler",
  "config": {
    "cam_poses": [
      {
        "number_of_samples": 10,
        "min_interest_score": 0.15,
        "proximity_checks": {
          "min": 1.0,
          "avg": {
            "min": 2.5,
            "max": 3.5,
          },
          "no_background": True
        },
        "location": {
          "provider":"sampler.Uniform3d",
          "max":[0, 0, 1.8],
          "min":[0, 0, 1.4]
        },
        "rotation": {
          "value": {
            "provider":"sampler.Uniform3d",
            "max":[1.338, 0, 6.283185307],
            "min":[1.2217, 0, 0]
          }
        }
      }
    ]
  }
}
```

* This module samples camera poses in the loaded 3D Front scenes
* It will create 10 different camera poses, based on the `number_of_samples`
* It will ensure that the min_interest_score is above 0.25, which means that there must be a variety of objects in the scene, this avoids that there are pictures of an empty corridor
* The proximity checks have several conditions:
  * the camera can not be closer than 1.0 (meters) to any object, be aware that we use a sparse sampling here, which might over look thin objects
  * the average of distance values must lie between 2.5 and 3.5 meters
  * And there are no background pixels allowed, which means the camera will not look out of one of the open windows or doors
* The location and rotation are only added here to the sampled locations. Each sampled location is in one of the rooms on the floor, we can now add a certain distance from the floor with the location sampling. The same is true for the rotation sampling. Each pose is validated against the criterias at the top and also if it is directly above the floor. So positions above a bed for example will be discarded. 
