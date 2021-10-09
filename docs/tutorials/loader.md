# Loading and manipulating objects

## Downloading assets

BlenderProc offers download functionality for many datasets and freely available assets via the `blenderproc` CLI:

* `blendeproc download_blenderkit`: Downloads materials and models from blenderkit
* `blendeproc download_haven`: Downloads HDRIs, Textures and Models from polyhaven.com.
* `blendeproc download_ikea`: Downloads the IKEA dataset.
* `blendeproc download_pix3d`: Downloads the Pix3D dataset.
* `blendeproc download_scenenet`: Downloads the scenenet dataset.

## Loading

BlenderProc provides various ways of importing your 3D models.
All loaders can be accessed via the `bproc.loader.load_*` methods, which all return the list of loaded `MeshObjects`.

```python
objs = bproc.loader.load_obj("mymesh.obj")
```

### Filetype-specific loaders:

* `bproc.loader.load_obj`: Loading .obj and .ply files.
* `bproc.loader.load_blend`: Loading from .blend files.

### Dataset-specific loaders:

* `bproc.loader.load_AMASS`: Loads objects from the AMASS Dataset.
* `bproc.loader.load_bop`: Loads the 3D models of any BOP dataset and allows replicating BOP scenes.
* `bproc.loader.load_front3d`: Loads 3D-Front scenes.
* `bproc.loader.load_ikea`: Loads objects from the IKEA dataset.
* `bproc.loader.load_pix3d`: Loads Pix3D objects.
* `bproc.loader.load_replica`: Loads scenes from the Replica dataset.
* `bproc.loader.load_scenenet`: Loads SceneNet scenes.
* `bproc.loader.load_shapenet`: Loads objects from the ShapeNet dataset.
* `bproc.loader.load_suncg`: Loads SUNCG scenes.

## Manipulating objects

As mentioned above, the loaders return a list of `MeshObjects`.
Each of these objects can be manipulated in various ways:

### Changing poses

Changing the location of an object can be done via:

```python
obj.set_location([2, 0, 1])
```

Setting the rotation via euler angles:

```python
obj.set_rotation_euler([np.pi, 0, 0])
```

Or setting the full pose via the 4x4 local-to-world transformation matrix:

```python
obj.set_local2world_mat(tmat)
```

Or applying a 4x4 transformation matrix on the current pose:

```python
obj.apply_T(tmat)
```

### More information

For more information look at the reference manual of `MeshObject`. TODO