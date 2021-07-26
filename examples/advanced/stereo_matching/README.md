# Stereo Matching
![](stereo_pair.png)
![](stereo_depth.png)

In the first row we can see the rendered stereo RGB images, left and right respectively, and beneath them we can view
the computed depth image using stereo matching. Note that due to a high discrepancy between the TV and the rest
of the rendered scene, the visualization is not descriptive enough. This discrepancy or high depth values at the TV
is due to a lack of gradient or useful features for stereo matching in this area. However, the depth values in other
areas are consistent and close to the rendered depth images.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/advanced/stereo_matching/config.yaml <path to cam_pose file> <path to house.json> examples/advanced/stereo_matching/output
```

* `examples/advanced/stereo_matching/config.yaml`: path to the configuration file with pipeline configuration.
* `<path to cam_pose file>`: Should point to a file which describes one camera pose per line (here the output of `scn2cam` from the `SUNCGToolbox` can be used).
* `<path to house.json>`: Path to the house.json file of the SUNCG scene you want to render. Which should be either located inside the SUNCG directory, or the SUNCG directory path should be added to the config file.
* `examples/advanced/stereo_matching/output`: path to the output directory.

## Visualizaton
Visualize the generated data:
```
python scripts/visHdf5Files.py examples/advanced/stereo_matching/output/1.hdf5
```

## Steps

* Loads a SUNCG scene: `loader.SuncgLoader` module.
* Loads camera positions from a given file: `camera.CameraLoader` module.
* Automatically adds light sources inside each room: `lighting.SuncgLighting` module.
* Renders semantic segmentation map: `renderer.SegMapRenderer` module.
* Renders rgb, depth and normals in stereo mode: `renderer.RgbRenderer` module.
* Computes depth based on stereo matching: `writer.StereoGlobalMatchingWriter` module
* Merges all into an `.hdf5` file: `writer.Hdf5Writer` module.

## Config file

```
"pip": [
      "h5py",
      "python-dateutil==2.1",
      "numpy",
      "Pillow",
      "opencv-contrib-python",
      "scipy"
    ]
```

Make sure these python packages are included.

```yaml
"global": {
  "output_dir": "<args:2>",
  "resolution_x": 1280,
  "resolution_y": 720
}
```

Indicate the desired output image resolution globally inside of the settings of the `"main.Initializer"`.

```yaml
{  
  "module": "camera.CameraLoader",
  "config": {
    "path": "<args:0>",
    "file_format": "location rotation/value _ _ _ _ _ _",
    "source_frame": ["X", "-Z", "Y"],
    "default_cam_param": {
      "rotation": {
        "format": "forward_vec"
      }
    },
    "intrinsics": {
      "interocular_distance": 0.05,
      "stereo_convergence_mode": "PARALLEL",
      "convergence_distance": 0.00001,
      "cam_K": [650.018, 0, 637.962, 0, 650.018, 355.984, 0, 0 ,1],
      "resolution_x": 1280,
      "resolution_y": 720
    },
  }
}
```
Here we specify the camera parameters, some notable points are:
* Setting the `interocular_distance` which is the stereo baseline.
* Specifying `stereo_convergence_mode` to be parallel (i.e. both cameras lie on the same line and are just shifted by `interocular_distance`, and are trivially coplanar).
    * Other options are `OFF-AXIS` where the cameras rotate inwards (converge) up to some plane.  
    * Check `camera.CameraModule`'s documentation for more info.
* `Convergence_distance` is the distance from the cameras to the aforementioned plane they converge to in case of `OFF-AXIS` convergence mode. In this case, this parameter is ignored by Blender, but it is added here for clarification.
* Adding a camera matrix in `cam_K`.
* Adding the image resolution once again in `intrinsics`, since this nested parameter is not on the same level as the global parameters, and thus the global parameters won't affect any configuration inside `intrinsics`.

```yaml
{
  "module": "renderer.RgbRenderer",
  "config": {
    "render_distance": true,
    "render_normals": true,
    "stereo": true
  }
}
```
We enable stereo rendering here. Also notice the order of the modules, where the stereo RGB rendering should be added before stereo matching. Orderings generally reflect dependencies.

```yaml
{
  "module": "writer.StereoGlobalMatchingWriter",
  "config": {
    "focal_length": 650.018,
    "disparity_filter": false
  }
}
```
Finally, we add the module responsible for stereo matching. This module has the following attributes and configurations:
* It is based on OpenCV's [implementation](https://docs.opencv.org/2.4/modules/calib3d/doc/camera_calibration_and_3d_reconstruction.html?highlight=sgbm#stereosgbm-stereosgbm) of [stereo semi global matching](https://elib.dlr.de/73119/1/180Hirschmueller.pdf).
* Its pipeline runs as follows:
    * Compute the disparity map between the two images. After specifying the required parameters.
    * Optional use of a disparity filter (namely `wls_filter`). Enabled by setting `disparity_filter` (Enabling it could possibly lead to less accurate depth values. One should experiment with this parameter).
    * Triangulate the depth values using the focal length and disparity.
    * Clip the depth map from 0 to `depth_max`, where this value is retrieved from `renderer.Renderer`.
    * Apply an optional [depth completion routine](https://github.com/kujason/ip_basic/blob/master/ip_basic/depth_map_utils.py), based on simple image processing techniques. This is enabled by setting `depth_completion`.
    * Finally, save the resulting depth map and optionally the disparity map in the .hdf5 file that contains the rendered outputs with keys: `stereo-depth` and `disparity` respectively. This is handled by the module: `writer.Hdf5Writer`.
* The focal length can be either set manually, or inferred from the field of view angle that in this case should be supplied to the CameraModule. To specify how it should be retrieved, use this config parameter: `infer_focal_length_from_fov`
* There are some stereo semi global matching parameters that can be configured from the config file, such as:
    * `window_size`
    * `num_disparities`
    * `min_disparity`
    * These are usually the most important parameters that need to be tuned. It is advisable that you try the `StereoGlobalMatchingWriter` externally on a few test images 
    to tune the parameters, and then apply it in BlenderProc.
