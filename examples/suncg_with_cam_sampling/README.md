# SUNCG scene with custom camera sampling

![](output-summary.png)

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py examples/suncg_with_cam_sampling/config.yaml <path to house.json> examples/suncg_with_cam_sampling/output
```

In contrast to the SUNCG basic example, we do here not load precomputed camera poses, but sample them using the `SuncgCameraSampler` module.

## Steps

* Loads a SUNCG scene
* Sample camera positions inside every room
* Automatically adds light sources inside each room
* Renders color, normal, segmentation and a depth images
* Merges all into an `.hdf5` file

## Explanation of specific parts of the config file

### SuncgCameraSampler

```yaml
{
  "name": "camera.SuncgCameraSampler",
  "config": {
    "proximity_checks": {
      "min": 1.0
    },
    "min_interest_score": 0.4
  }
},
```
* This module goes through all rooms of the loaded house and samples camera poses inside them randomly
* After sampling a pose the pose is only accepted if it is valid according to the properties we have specified:
  * Per default a camera pose is only accepted, if there is no object between it and the floor
  * As we enabled `proximity_checks` with a `min` value of `1.0`, we then only accept the pose if every object in front of it is at least 1 meter away
  * At the end we also check if the sampled view is interesting enough. Therefore a score is calculated based on the number of objects that are visible and how much space they occupy. Only if the score is above `0.4` the pose is accepted.

  