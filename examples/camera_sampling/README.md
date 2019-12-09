# Camera sampling

![](rendering.png)

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py examples/camera_sampling/config.yaml examples/camera_sampling/output
```

This example explains how to sample random camera positions that all look towards the point of interest.

## Steps

* Loads `scene.obj`
* Creates a point light
* Samples camera positions randomly above the plane looking to the POI
* Renders normals
* Renders rgb

## Explanation of the config file

### Camera sampling
```yaml
{
  "name": "camera.CameraSampler",
  "config": {
    "cam_poses": [
      {
        "location": {
          "name":"Uniform3dSampler",
          "parameters":{
            "max":[10, 10, 8],
            "min":[-10, -10, 12]
          }
        },
        "look_at_point": {
          "name": "POIGetter",
          "parameters": {}
        },
        "rotation_format": "look_at"
      }
    ]
  }
},
```

* Sample location uniformly in a bounding box above the plane
* Calculate orientation be setting the look at point to the POI
* The POI is calculated from the position of all objects
 
