# Stereo Matching
<p align="center">
<img src="../../../images/stereo_matching_color_left.jpg" alt="Front readme image" width=400>
<img src="../../../images/stereo_matching_color_right.jpg" alt="Front readme image" width=400>
</p>
<p align="center">
<img src="../../../images/stereo_matching_stereo_depth.jpg" alt="Front readme image" width=400>
</p>

In the first row we can see the rendered stereo RGB images, left and right respectively, and beneath them we can view
the computed depth image using stereo matching. The high depth values from the uniform yellow area to the right are due to a lack of gradient or useful features for stereo matching in this area. However, the depth values in other
areas are consistent and close to the rendered depth images.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/stereo_matching/main.py <path to cam_pose file> <path to house.json> examples/advanced/stereo_matching/output
```

* `examples/advanced/stereo_matching/main.py`: path to the main python file to run.
* `<path to cam_pose file>`: Should point to a file which describes one camera pose per line (here the output of `scn2cam` from the `SUNCGToolbox` can be used).
* `<path to house.json>`: Path to the house.json file of the SUNCG scene you want to render. Which should be either located inside the SUNCG directory, or the SUNCG directory path should be added to the config file.
* `examples/advanced/stereo_matching/output`: path to the output directory.

## Visualizaton
Visualize the generated data:
```
blenderproc vis hdf5 examples/advanced/stereo_matching/output/1.hdf5
```

## Implementation

```python
# Enable stereo mode and set baseline
bproc.camera.set_stereo_parameters(interocular_distance=0.05, convergence_mode="PARALLEL")
```

Here we enable stereo rendering and specify the camera parameters, some notable points are:
* Setting the `interocular_distance` which is the stereo baseline.
* Specifying `convergence_mode` to be `"PARALLEL"` (i.e. both cameras lie on the same line and are just shifted by `interocular_distance`, and are trivially coplanar).
    * Other options are `OFF-AXIS` where the cameras rotate inwards (converge) up to some plane.  
  * `convergence_distance` is the distance from the cameras to the aforementioned plane they converge to in case of `OFF-AXIS` convergence mode. In this case, this parameter is ignored by Blender, but it is added here for clarification.

```python
# Apply stereo matching to each pair of images
data["stereo-depth"], data["disparity"] = bproc.postprocessing.stereo_global_matching(data["colors"], disparity_filter=False)
```

Here we apply the stereo matching.
* It is based on OpenCV's [implementation](https://docs.opencv.org/2.4/modules/calib3d/doc/camera_calibration_and_3d_reconstruction.html?highlight=sgbm#stereosgbm-stereosgbm) of [stereo semi global matching](https://elib.dlr.de/73119/1/180Hirschmueller.pdf).
* Its pipeline runs as follows:
    * Compute the disparity map between the two images. After specifying the required parameters.
    * Optional use of a disparity filter (namely `wls_filter`). Enabled by setting `disparity_filter` (Enabling it could possibly lead to less accurate depth values. One should experiment with this parameter).
    * Triangulate the depth values using the focal length and disparity.
    * Clip the depth map from 0 to `depth_max`, where this value is retrieved from `renderer.Renderer`.
    * Apply an optional [depth completion routine](https://github.com/kujason/ip_basic/blob/master/ip_basic/depth_map_utils.py), based on simple image processing techniques. This is enabled by setting `depth_completion`.
* There are some stereo semi global matching parameters that can be tuned (see fct docs), such as:
    * `window_size`
    * `num_disparities`
    * `min_disparity`