# Configuring the camera

## Intrinsics

There a multiple ways of setting the intrinsics of the camera.

### K matrix

The simplest way is to just set the instrinsics via a 3x3 K-matrix.

```python
bproc.camera.set_intrinsics_from_K_matrix(K, image_width, image_height)
```

### Blender parameters

Alternatively, you can set blender camera parameters directly. 
This means either setting the focal length in mm:

```python
bproc.camera.set_intrinsics_from_blender_params(lens=focal_length)
```

Or setting the field of view:

```python
bproc.camera.set_intrinsics_from_blender_params(lens=field_of_view, lens_unit="FOV")
```

## Extrinsics

Adding a new camera pose is done by specifying the 4x4 transformation matrix from camera to world coordinate system.

```python
bproc.camera.add_camera_pose(tmat)
```

Each time this is method is called, a new key frame is added with the given camera pose assigned to it.
When calling the renderer afterwards the scene rendered from the view of all registered camera poses.
To learn more about how that works in detail, please read the [key frame](key_frames.md) chapter.