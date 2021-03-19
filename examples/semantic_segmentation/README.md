# Semantic Segmentation 

<p align="center">
<img src="rendering_0.png" alt="Front readme image" width=375>
<img src="rendering_1.png" alt="Front readme image" width=375>
</p>

The focus of this example is to introduce user to `renderer.SegMapRenderer` module, which generates semantic segmentations of scenes.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/semantic_segmentation/config.yaml examples/semantic_segmentation/camera_positions examples/semantic_segmentation/scene.blend examples/semantic_segmentation/output
```

* `examples/semantic_segmentation/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/semantic_segmentation/camera_positions`: text file with parameters of camera positions.
* `examples/semantic_segmentation/scene.blend`: path to the blend file with the basic scene.
* `examples/semantic_segmentation/output`: path to the output directory.

## Steps

* Loads `scene.obj`: `loader.ObjectLoader` module, each object in this scene already contains a custom property `category_id`, which is later used in the `SegMapRenderer`. 
Without this idea it would not be possible to render the correct class.
* Creates a point light: `lighting.LightLoader` module.
* Loads camera positions from `camera_positions`: `camera.CameraLoader` module.
* Renders rgb and the distance: `renderer.RgbRenderer` module.
* Renders class segmentation: `renderer.SegMapRenderer` module.
* Writes the images into `.hdf5` containers: `writer.Hdf5Writer` module.

## Config file

### BlendLoader

```yaml
{
  "module": "loader.BlendLoader",
  "config": {
    "path": "<args:1>"
  }
}
```

This loads the `.blend` file, it extracts hereby only the mesh objects from the file, not all information stored in this `.blend` file.

### WorldManipulator

```yaml
{
  "module": "manipulators.WorldManipulator",
  "config": {
    "cf_set_world_category_id": 0  # this sets the worlds background category id to 0
  }
}
```

This module does sets the world background to the `category_id` 0, this is necessary for the `SegMapRenderer`. 

### SegMapRenderer
```yaml
{
  "module": "renderer.SegMapRenderer",
  "config": {
    "map_by": ["class", "instance", "name"]
  }
}
```

This module can map any kind of object related information to an image or to a list of indices of the objects in the scene.
So, if you want to map the custom property `category_id` to an image, you write `"map_by": "class"`.
Then each pixel gets assigned the `category_id` of the object present in that pixel.
If it is set to `instance` each pixel gets an id for the obj nr in the scene, these are consistent for several frames, which also means that not all ids must appear in each image.
It can also be set to different custom properties or attributes of the object class like: `"name"`, which returns the name of each object. 
This can not be saved in an image, so a csv file is generated, which is attached to the `.hdf5` container in the end.
Where it maps each instance nr to a name. 
If there are keys, which can not be stored in an image, it is necessary to also generate a instance image.
Furthermore, if an instance image is used all other used keys are stored in the .csv.

For example it would also be possible to use the key: `"location"`. This would access the location of each object and add it to the csv file.
Be aware that if the background is visible this will raise an error, as the background has no `location` attribute.
This can be avoided by providing a default value like: `default_values: {"location: [0,0,0]}`.

### Hdf5Writer

```yaml
{
  "module": "writer.Hdf5Writer",
  "config": {
    "postprocessing_modules": {
      "distance": [
      {"module": "postprocessing.TrimRedundantChannels"},
      {"module": "postprocessing.Dist2Depth"}
      ]
    }
  }
}
```
This combines as before all rendered images per camera pose into one `.hdf5` container.
Before this happens there are two modules executed on the output of the `RgbRenderer`, which creates a distance image.
Each pixel corresponding to the Z-Buffer value, this is however not the same as `depth` image. 
We therefore here convert this image into a `depth` image by using the `Dist2Depth` module.
The `TrimRedundantChannels` decreases the amount of channels in the `distance/depth` image to 1 instead of 3.
