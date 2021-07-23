# SUNCG scene with custom camera sampling

![](output-summary.png)

In contrast to the SUNCG basic example, we do here not load precomputed camera poses, but sample them using the `SuncgCameraSampler` module.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/datasets/suncg_with_cam_sampling/config.yaml <path to house.json> examples/datasets/suncg_with_cam_sampling/output
```

* `examples/datasets/suncg_with_cam_sampling/config.yaml`: path to the configuration file with pipeline configuration.
* `<path to house.json>`: Path to the house.json file of the SUNCG scene you want to render.
* `examples/datasets/suncg_with_cam_sampling/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/datasets/suncg_with_cam_sampling/output/0.hdf5
```

## Steps

* Loads a SUNCG scene: `loader.SuncgLoader` module.
* Sample camera positions inside every room: `camera.SuncgCameraSampler` module.
* Automatically adds light sources inside each room: `lighting.SuncgLighting` module.
* Writes sampled camera poses to file: `writer.CameraStateWriter` module.
* Renders semantic segmentation map: `renderer.SegMapRenderer` module.
* Renders rgb, distance and normals: `renderer.RgbRenderer` module.
* Merges all into an `.hdf5` file: `writer.Hdf5Writer` module.

## Config file

### SuncgCameraSampler

```yaml
{
  "module": "camera.SuncgCameraSampler",
  "config": {
    "cam_poses": [{
      "number_of_samples": 10,
      "proximity_checks": {
        "min": 1.0
      },
      "min_interest_score": 0.4,
      "location": {
        "provider":"sampler.Uniform3d",
        "max":[0, 0, 2],
        "min":[0, 0, 0.5]
      },
      "rotation": {
        "value": {
          "provider":"sampler.Uniform3d",
          "max":[1.2217, 0, 6.283185307],
          "min":[1.2217, 0, 0]
        }
      },
    }]
  }
}
```

With this module we want to sample `10` valid camera poses inside the loaded SUNCG rooms. 
The x and y coordinate are hereby automatically sampled uniformly across a random room, while we configure the z coordinate to lie between `0.5m` and `2m` above the ground.
Regarding the camera rotation we fix the pitch angle to `70°`, the roll angle to `0°` and sample the yaw angle uniformly between `0°` and `360°`. 

After sampling a pose the pose is only accepted if it is valid according to the properties we have specified:
  * Per default a camera pose is only accepted, if there is no object between it and the floor
  * As we enabled `proximity_checks` with a `min` value of `1.0`, we then only accept the pose if every object in front of it is at least 1 meter away
  * At the end we also check if the sampled view is interesting enough. Therefore a score is calculated based on the number of objects that are visible and how much space they occupy. Only if the score is above `0.4` the pose is accepted.
  
