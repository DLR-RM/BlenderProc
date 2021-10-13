# Random Room Constructor

<p align="center">
<img src="../../../images/random_room_constructor_rendered_example.jpg" alt="Front readme image" width=400>
</p>

This example explains the `RandomRoomConstructor`. This module can build random rooms and place objects loaded from other modules inside of it.

This current example uses the `CCMaterialLoader`. So download the textures from cc_textures we provide a script [here](../../scripts/download_cc_textures.py).
It also uses the `IkeaLoader`, for that please see the [ikea example](../ikea/README.md). 

Both are needed to use to this example.

## Usage

Execute in the BlenderProc main directory:

```
blenderproc run examples/advanced/random_room_constructor/main.py resources/ikea resources/cctextures examples/advanced/random_room_constructor/output
``` 

* `<PATH_TO_IKEA>`: path to the downloaded IKEA dataset, see the [scripts folder](../../scripts) for the download script. 
* `resources/cctextures`: path to CCTextures folder, see the [scripts folder](../../scripts) for the download script.
* `examples/advanced/random_room_constructor/output`: path of the output directory.

Make sure that you have downloaded the `ikea` dataset and the `cctextures` before executing.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
blenderproc vis hdf5 examples/advanced/random_room_constructor/output/*.hdf5
``` 

## Implementation


```python
# Load materials and objects that can be placed into the room
materials = bproc.loader.load_ccmaterials(args.cc_material_path, ["Bricks", "Wood", "Carpet", "Tile", "Marble"])
interior_objects = []
for i in range(15):
    interior_objects.extend(bproc.loader.load_ikea(args.ikea_path, ["bed", "chair", "desk", "bookshelf"]))
```
Loads the `cctextures` downloaded via the script, here only the assets which have one of the names of the list in their name are used. This makes it more realistic as things like `"Asphalt"` are not commonly found inside. Also loads 15 objects from the specified categories of the ikea dataset.

```python
# Construct random room and fill with interior_objects
objects = bproc.constructor.construct_random_room(used_floor_area=25,   
                                                  interior_objects=interior_objects,
                                                  materials=materials, amount_of_extrusions=5)
```

`construct_random_room` constructs a random floor plane and builds the corresponding wall and ceiling. It places the loaded ikea objects at random positions and sets cc-texture materials.
The room will have a floor area of 25 square meters, and it will have at most 5 extrusions. 
An extrusion is a corridor, which stretches away from the basic rectangle in the middle. 
These can be wider or smaller, but never smaller than the minimum `corridor_width`.
The module will automatically split the 25 square meter over all extrusions.

```python
# Bring light into the room
bproc.lighting.light_surface([obj for obj in objects if obj.get_name() == "Ceiling"], emission_strength=4.0)
```
Let the ceiling emit light and remove any materials placed on it. 
