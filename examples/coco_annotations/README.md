# Basic scene

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py examples/coco_annotations/config.yaml examples/coco_annotations/camera_positions examples/coco_annotations/scene.obj examples/coco_annotations/output
```

Here `examples/basic/config.yaml` is the config file which defines the structure and properties of the pipeline.
The three arguments afterwards are used to fill placeholders like `<args:0>` inside this config file. 

## Steps

* Loads `scene.obj`
* Creates a point light
* Loads camera positions from `camera_positions`
* Renders normals
* Renders rgb
* Renders instance segmentation
* writes coco annotations

## Explanation of the config file
 
 Please look at basic example to understand the working of all parts of config.yaml except coco annotation writer

#### CocoAnnotationsWriter

```yaml
  {
    "name": "writer.CocoAnnotationsWriter",
    "config": {
    }
  }
```
This modules depends on output from 'renderer.SegMapRenderer' and stores annotations in coco_annotations.json.


### Visualizing Annotations

You can use vis_annotation.py like following to visualize annotation over a rendered rgb image.

```
python vis_annotation.py -i <image index> -c <coco annotaions json file> -b <base path for the files>
```

#### Working Examples
With specific values
```
python vis_annotation.py -i 1 -c coco_annotations.json -b output
```

With default values
```
python vis_annotation.py
```