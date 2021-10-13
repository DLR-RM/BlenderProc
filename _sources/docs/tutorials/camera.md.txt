# Configuring the camera

## Intrinsics

There are multiple ways of setting the intrinsics of the camera.

### K matrix

The simplest way is to just set the intrinsics via a 3x3 K-matrix.

```python
K = np.array([
    [fx, 0, cx],
    [0, fy, cy],
    [0, 0, 1]
])
bproc.camera.set_intrinsics_from_K_matrix(K, image_width, image_height)
```

### Blender parameters

Alternatively, you can set blender camera parameters directly. 
This means either setting the focal length in mm:

```python
bproc.camera.set_intrinsics_from_blender_params(lens=focal_length, lens_unit="MILLIMETERS")
```

Or setting the field of view:

```python
bproc.camera.set_intrinsics_from_blender_params(lens=field_of_view, lens_unit="FOV")
```

## Extrinsics

Adding a new camera pose is done by specifying the 4x4 transformation matrix from camera to world coordinate system.

```python
bproc.camera.add_camera_pose(tmat) # tmat is a 4x4 numpy array
```

Each time this method is called, a new key frame is added with the given camera pose assigned to it.
When calling the renderer afterwards the scene is rendered from the view of all registered camera poses.
To learn more about how that works in detail, please read the [key frame](key_frames.md) chapter.

Blender uses the OpenGL coordinate frame. 
So, if you want to use camera poses that are specified in OpenCV coordinates, you need to transform them first.
To do so, you can use the following utility function:
```python
# OpenCV -> OpenGL
cam2world = bproc.math.change_source_coordinate_frame_of_transformation_matrix(cam2world, ["X", "-Y", "-Z"])
```

--- 

Next Tutorial: [Rendering the scene](renderer.md)
