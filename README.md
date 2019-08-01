# Blender-Pipeline
A blender pipeline to generate images for deep learning

## How to render a scene

Here is how to render multiple views from the scene `002fa647848abeff3c969cc0bc1bb8b6`.

First create the .obj file containing the house:
```
cd <suncg>/house/002fa647848abeff3c969cc0bc1bb8b6
scn2scn house.json /tmp/house.obj
```

Call blender (>= v2.79b) script to render all views from given camera pose file into the given <output_dir>.
```
python run.py config/suncg_basic.json <cams>/002fa647848abeff3c969cc0bc1bb8b6/outputCamerasFile <houses>/002fa647848abeff3c969cc0bc1bb8b6/house.json
```
