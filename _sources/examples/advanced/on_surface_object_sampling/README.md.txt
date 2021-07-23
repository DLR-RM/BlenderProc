# On surface object pose Sampling

![](rendering.png)

The focus of this example is the `OnSurfaceSampler` which allows pose sampling for some selected objects on top of a selected surface.

## Usage

Execute this in the BlenderProc main directory:

```
python run.py examples/advanced/on_surface_object_sampling/config.yaml examples/resources/camera_positions examples/advanced/on_surface_object_sampling/scene.blend examples/advanced/on_surface_object_sampling/output
```

* `examples/advanced/on_surface_object_sampling/config.yaml`: path to the configuration file with pipeline configuration.
* `examples/resources/camera_positions`: text file with parameters of camera positions.
* `examples/advanced/on_surface_object_sampling/scene.blend`: path to the object file with the basic scene.
* `examples/advanced/on_surface_object_sampling/output`: path to the output directory.

## Visualization

Visualize the generated data:

```
python scripts/visHdf5Files.py examples/advanced/on_surface_object_sampling/output/0.hdf5
```

## Steps

* Loads all objects from `scene.blend`: `loader.BlendLoader` module.
* Set selected objects as active: `manipulators.EntityManipulator` module.
* Set selected objects as passive: `manipulators.EntityManipulator` module.
* Sample selected object poses on top a selected surface: `object.OnSurfaceSampler` module.
* Runs the physics simulation: `object.PhysicsPositioning` module.
* Creates a point light: `lighting.LightLoader` module.
* Sets two camera positions: `camera.CameraLoader` module.
* Renders rgb: `renderer.RgbRenderer` module.
* Writes the output to .hdf5 containers: `writer.Hdf5Writer` module.

## Config file

### OnSurfaceSampler

```yaml
{
  "module": "object.OnSurfaceSampler",
  "config": {
    "objects_to_sample": {                      # mesh objects to sample on the surface
      "provider": "getter.Entity",
      "conditions": {
        "name": ".*phere.*"                     # we select all UV spheres and Icospheres
      }
    },
    "surface": {                                # the object to use as a surface to sample on
      "provider": "getter.Entity",              
      "index": 0,                               # make sure the Provider returns only one object
      "conditions": {
        "name": "Cube"                          # Cube in the scene is selected
      }
    },
    "pos_sampler": {
      "provider": "sampler.UpperRegionSampler",
      "to_sample_on": {                         # select it again, but inside the sampler to define the upper region the space above the Cube
        "provider": "getter.Entity",
        "index": 0,                             # returns only the first object to satisfy the conditions
        "conditions": {
          "name": "Cube"                        # same Cube is selected
        }
      },
      "min_height": 1,                          # points sampled in this space will have height varying in this min-max range
      "max_height": 4,                          # this range also helps the module to satisfy the non-intersecting bounding boxes checks for the sampled objects and the surface faster
      "use_ray_trace_check": False,
    },
    "min_distance": 0.1,                        # minimal distance between sampled objects
    "max_distance": 10,                         # and a maximal distance. The smaller the min-max range, the more tries the module can take to sample the appropriate location
    "rot_sampler": {                            # uniformly sample rotation
      "provider": "sampler.Uniform3d",
      "max": [0,0,0],
      "min": [6.28,6.28,6.28]
    }
  }
}
```

* invoke a `getter.Entity` Provider to select `objects_to_sample` - objects we want to sample poses for.
* invoke a `getter.Entity` Provider to select an object to use as a `surface` to sample on top (note `"index": 0` which ensures that Provider returns only one object.)
* sample positions for `objects_to_sample` via `sampler.UpperRegionSampler` (configure `min_height` and `max_height` such that sampled objects don't intersect with the `surface`).
* `min_distance` and `max_distance` define an acceptable range between sampled objects. The smaller the range, the more `max_iterations` (default is 100) may be required to successfully place an object.
* sample rotation for `objects_to_sample` using `sampler.Uniform3d` Provider.
