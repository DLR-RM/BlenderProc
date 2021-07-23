# COCO annotations

![](rendering.png)

The focus of this example is to introduce user to `writer.CocoAnnotationsWriter` module.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/advanced/coco_annotations/config.yaml examples/resources/camera_positions examples/advanced/coco_annotations/scene.blend examples/advanced/coco_annotations/output
```

* `examples/advanced/coco_annotations/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/resources/camera_positions`: text file with parameters of camera positions.
* `examples/advanced/coco_annotations/scene.blend`: path to the blend file with the basic scene.
* `examples/advanced/coco_annotations/output`: path to the output directory.

### Visualizing Annotations

You can use vis_coco_annotation.py with the following command to visualize the annotations blended over a rendered rgb image:

```
python scripts/vis_coco_annotation.py [-i <image index>] [-c <coco annotations json>] [-b <base folder of coco json and image files>]
```

### Working Examples

With specific values:

```
python scripts/vis_coco_annotation.py -i 1 -c coco_annotations.json -b examples/advanced/coco_annotations/output/coco_data
```

Above are also the default values, i.e. for the same result call:

```
python scripts/vis_coco_annotation.py
```

## Steps

* Loads `scene.blend`: `loader.BlendLoader` module. The `BlendLoader` is used here as we always load the `cp_category_id` for each object, which is stored in the `.blend` file.
* Creates a point light: `lighting.LightLoader` module.
* Loads camera positions from `camera_positions`: `camera.CameraLoader` module.
* Renders rgb: `renderer.RgbRenderer` module.
* Renders instance segmentation: `renderer.SegMapRenderer` module.
* Writes coco annotations: `writer.CocoAnnotationsWriter` module.
<!-- * Writes the output to .hdf5 containers: `writer.Hdf5Writer` module. -->

## Config file

### SegMapRenderer

```yaml
  {
    "module": "renderer.SegMapRenderer",
    "config": {
      "map_by": ["instance", "class", "name"],
    }
  }
```

The `renderer.SegMapRenderer` needs to render both instance and class maps. The class is defined in terms of a custom property `category_id` which must be previously defined for each instance. The `category_id` can be either set in a custom Loader module or in a `.blend` file.
We also add `"name"` to the mapping, s.t. we can later use the object's names for labeling the categories in the coco annotations writer. 

### CocoAnnotationsWriter

```yaml
  {
    "module": "writer.CocoAnnotationsWriter",
    "config": {
    }
  }
```

This modules depends on output from `renderer.SegMapRenderer` and stores annotations in `coco_annotations.json`. Optionally, you can set `"supercategory": "<some_supercategory>"` in the `writer.CocoAnnotationsWriter` config to filter objects by a previously assigned custom property `"supercategory"`.
