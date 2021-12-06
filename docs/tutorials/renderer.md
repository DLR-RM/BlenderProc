# Renderer

Each renderer renders every frame in the configured interval `[frame_start, frame_end - 1]`.
Afterwards, they return a dictionary containing the rendered images grouped by type, e.q:

```json
{
  "colors": [<np.uint8: [512, 512, 3]>, <np.uint8: [512, 512, 3]>],
  "normals": [<np.float32: [512, 512]>, <np.float32: [512, 512]>],
  "distance": [<np.float32: [512, 512]>, <np.float32: [512, 512]>]
}
```

Here the scene was rendered from the view of two camera poses with normals and distance output activated.


## RGB renderer

The RGB renderer is the main renderer which can be configured with a variety of API methods listed in the documentation.

```python
data = bproc.renderer.render()
```

### Depth, distance and normals

Without any additional overhead, the RGB renderer can output depth/distance and normal images.
These additional outputs can be activated by calling:

```python
bproc.renderer.enable_distance_output()
bproc.renderer.enable_depth_output()
bproc.renderer.enable_normals_output()
```

It is important to note the difference between depth and distance here:
By using `bproc.renderer.enable_distance_output()`, an antialiased distance image is rendered. To render a z-buffer depth image without any smoothing effects use `bproc.renderer.enable_depth_output()` instead. 
While distance and depth images sound similar, they are not the same: In [distance images](https://en.wikipedia.org/wiki/Range_imaging), each pixel contains the actual distance from the camera position to the corresponding point in the scene. 
In [depth images](https://en.wikipedia.org/wiki/Depth_map), each pixel contains the distance between the camera and the plane parallel to the camera which the corresponding point lies on.


### Samples & Denoiser

As blender uses a raytracer, the number of rays influences the required amount of computation and the noise in the rendered image.
The more rays are computed, the longer the rendering takes, but the more accurate and less noisy the resulting image is.
The noise level can be controlled by using `brpoc.renderer.set_noise_threshold(noise_threshold)`.
This means that for each pixel only so many rays are used to get below this noise threshold.
Hereby, `noise_threshold` is a float value above `0` and below `0.1`. 
A higher value means more noise per pixel, a lower value results in less noise but longer computation time.
You can influence the maximum amount of samples per pixel with the `bproc.rendererset_max_amount_of_samples(max_amount_of_samples)` fct.
For more information about how blenders renderer works visit the [blender docu](https://docs.blender.org/manual/en/latest/render/cycles/render_settings/sampling.html).

The required noise level is unfortunately quite low to achieve a smooth result and therefore rendering can take quite long.
To reduce the number of required samples per pixel, blender offers Denoiser to reduce the noise in the resulting image.
Set them via `bproc.renderer.set_denoiser`:

* `bproc.renderer.set_denoiser("INTEL")`: Activates Intels [Open Image Denoiser](https://www.openimagedenoise.org/)
* `bproc.renderer.set_denoiser(None)`: Deactivates any denoiser.

Per default "INTEL" is used. 

## Segmentation renderer

In segmentation images every pixel corresponding to the same object is set to the same object related number.
The kind of number that is used for a given object is determined by the `map_by` parameter:

* `"instance"`: Each object gets assigned a unique id (consistent across all frames), s.t. the resulting images can be used for instane segmentation.
* `"class"`: The custom property `category_id` of each object is used, which usually results in semantic segmentation images.
*  Addionally, any other attribute / custom property can be used. If the attribute is not a number, an instance segmentation image is returned together with a mapping from instance id to the desired non-numerical attribute.

When multiple`map_by` parameters are given, then also multiple segmentation maps are returned or - if the corresponding attribute is non-numeric - addional mappings are returned in `instance_attribute_maps`.

For example:

```python
data = bproc.renderer.render_segmap(map_by=["instance", "class", "name"])
```

The returned data will contain (assuming two registered frames / camera poses):

```json
{
  "instance_segmaps": [<np.array, [512, 512]>, <np.array, [512, 512]>],
  "class_segmaps": [<np.array, [512, 512]>, <np.array, [512, 512]>],
  "instance_attribute_maps": [
    [{"idx": 0, "name":  "<object_name_0>"}, {"idx": 1, "name":  "<object_name_1>"}, ...],
    [{"idx": 0, "name":  "<object_name_0>"}, {"idx": 1, "name":  "<object_name_1>"}, ...]
  ],
}
```

For names the mapping will stay the same across different frames, however, there are attributes that can change from frame to frame. 
Thats why `instance_attribute_maps` are also given per frame.

## Optical flow renderer

Rendering the (forward/backward) optical flow between consecutive frames can be done via:
```python
data = bproc.renderer.render_optical_flow()
```

Here each pixel describes the change from the current frame to the next (forward) or the previous (backward) frame.

--- 

Next tutorial: [Writing the results to file](writer.md)
