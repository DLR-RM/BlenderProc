# Loading and manipulating objects

## Downloading assets

If don't have any data yet, BlenderProc offers download functionality for many datasets and freely available assets via the `blenderproc` CLI:

* `blenderproc download blenderkit <output_dir>`: Downloads materials and models from blenderkit
* `blenderproc download cc_textures <output_dir>`: Downloads textures from cc0textures.com.
* `blenderproc download haven <output_dir>`: Downloads HDRIs, Textures and Models from polyhaven.com.
* `blenderproc download ikea <output_dir>`: Downloads the IKEA dataset. **(At the moment this dataset is not availabe! Use pix3d instead, as ikea is a subset of pix3D)**
* `blenderproc download pix3d <output_dir>`: Downloads the Pix3D dataset.
* `blenderproc download scenenet <output_dir>`: Downloads the scenenet dataset.
* `blenderproc download matterport3d <output_dir>`: Downloads the Matterport3D dataset.

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
* `bproc.loader.load_bop_objs`: Loads the 3D models of any BOP dataset and allows replicating BOP scenes.
* `bproc.loader.load_bop_scene`: Loads any real BOP scenes using 3D models.
* `bproc.loader.load_bop_intrinsics`: Loads intrinsics of specified BOP dataset.
* `bproc.loader.load_front3d`: Loads 3D-Front scenes.
* `bproc.loader.load_ikea`: Loads objects from the IKEA dataset.
* `bproc.loader.load_pix3d`: Loads Pix3D objects.
* `bproc.loader.load_replica`: Loads scenes from the Replica dataset.
* `bproc.loader.load_scenenet`: Loads SceneNet scenes.
* `bproc.loader.load_shapenet`: Loads objects from the ShapeNet dataset.
* `bproc.loader.load_suncg`: Loads SUNCG scenes.
* `bproc.loader.load_matterport3d`: Loads a Matterport3D scene.

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

## Custom properties

If you have any user-specific attributes that you want to assign to objects, you should use custom properties.
In a key-value like fashion you can assign any desired value to a given object.

This is how you set a custom property:
```python
obj.set_cp("my_prop", 42)
```

And that is how you retrieve one:
```python
obj.get_cp("my_prop")
```

### More information

For more information look at the reference manual of `MeshObject`.

--- 

Next tutorial: [Configuring the camera](camera.md)
