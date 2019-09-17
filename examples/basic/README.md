# Basic scene

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py examples/basic/config.json examples/basic/camera_positions examples/basic/scene.obj examples/basic/output
```

## Steps

* Loads `scene.obj`
* Creates a point light
* Loads camera positions from `camera_positions`
* Renders normals
* Renders rgb