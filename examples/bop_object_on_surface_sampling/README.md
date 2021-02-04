# BOP object on textured surface sampling

![](rendering.png)

Here we explain the on surface sampling config used for the synthetic data generation in the BOP Challenge 2020. BOP objects from specified datasets are randomly chosen and placed upright onto a plane inside a cube with randomized PBR textures. Object material properties and light sources are also randomized. Samples cameras looking at objects. Outputs RGB, depth, camera intrinsics and object poses in BOP format.

## Usage

Make sure that you downloaded the [BOP datasets](https://bop.felk.cvut.cz/datasets/). 

Execute in the BlenderProc main directory:

```
python scripts/download_cc_textures.py 
```

```
python run.py examples/bop_object_on_surface_sampling/config.yaml 
              <path_to_bop_data> 
              <bop_dataset_name> 
              <path_to_bop_toolkit> 
              resources/cctextures 
              examples/bop_object_on_surface_sampling/output
``` 

* `examples/bop_object_on_surface_sampling/config.yaml`: path to the pipeline configuration file.
* `<path_to_bop_data>`: path to a folder containing BOP datasets.
* `<bop_dataset_name>`: name of BOP dataset for which ground truth should be saved, e.g. lm
* `<path_to_bop_toolkit>`: path to a bop_toolkit folder.
* `resources/cctextures`: path to CCTextures folder
* `examples/bop_object_on_surface_sampling/output`: path to an output folder.

## Generate a dataset
To aggregate data and labels over multiple scenes, simply run the script multiple times using the same command. As data is saved in chunks of 1000 images, you can easily distribute the data generation by running the scripts on different machines/servers and then collecting all chunks.

## Steps

* Load T-LESS BOP models: `loader.BopLoader` module.
* Load LM BOP models: `loader.BopLoader` module.
* Load `<args:1>` (YCB-V) BOP models: `loader.BopLoader` module.
* Sample colors for T-LESS models: `manipulators.MaterialManipulator` module.
* Sample roughness and specular values for all objects: `manipulators.MaterialManipulator` module.
* Construct planes: `constructor.BasicMeshInitializer` module.
* Set custom properties for those planes: `manipulators.EntityManipulator` module.
* Switch to a light emission shader for the top plane: `manipulators.MaterialManipulator` module.
* Load CCTexture materials: `loader.CCMaterialLoader` module.
* Sample a material for the other planes: `manupulators.EntityManipulator` module.
* Sample upright objects poses on surface: `object.OnSurfaceSampler` module.
* Sample point light source: `lighting.LightSampler` module.
* Sample camera poses: `camera.CameraSampler` module.
* Render RGB and distance: `renderer.RgbRenderer` module.
* Write BOP data: `writer.BopWriter` module.

## Config file

### BOP Loader

```yaml
    {
      "module": "loader.BopLoader",
      "config": {
        "bop_dataset_path": "<args:0>/tless",
        "model_type": "cad",
        "mm2m": True,
        "sample_objects": True,
        "num_of_objs_to_sample": 3,
        "add_properties": {
          "cp_physics": True
        }
      }
    }
```
```yaml
    {
      "module": "loader.BopLoader",
      "config": {
        "bop_dataset_path": "<args:0>/lm",
        "model_type": "",
        "mm2m": True,
        "sample_objects": True,
        "num_of_objs_to_sample": 3,
        "add_properties": {
          "cp_physics": True
        },
        "cf_set_shading": "SMOOTH"
      }
    }
```
```yaml
    {
      "module": "loader.BopLoader",
      "config": {
        "bop_dataset_path": "<args:0>/<args:1>",
        "model_type": "",
        "mm2m": True,
        "sample_objects": True,
        "num_of_objs_to_sample": 10,
        "add_properties": {
          "cp_physics": True
        },
        "cf_set_shading": "SMOOTH"
      }
    }
```

* Here we are sampling BOP objects from 3 different datasets.
* We load 3 random objects from LM and T-LESS datasets, and 10 objects from the dataset given by `"<args:1>"` (e.g. ycbv in this case).
* `"cf_set_shading": "SMOOTH"` sets the shading for these corresponding objects to smooth. This looks more realistic for coarser + curved meshes like in LineMOD. For T-LESS and ITODD it should be ommited in favor of flat shading which appears more realistic on edgy objects. 
* Note that each loader loads the camera intrinsics and resolutions of each dataset, thus each subsequent `BopLoader` module overwrites these intrinsics. In this example, `"<args:1>"`(ycbv) dataset intrinsics are used when rendering. If required, they can be overwritten by setting `resolution_x, resolution_y, cam_K` in the camera sampler or global config.

### Material Manipulator

```yaml
    {
      "module": "manipulators.MaterialManipulator",
      "config": {
        "selector": {
          "provider": "getter.Material",
          "conditions": [
          {
            "name": "bop_tless_vertex_col_material.*"
          }
          ]
        },
        "cf_set_base_color": {
          "provider": "sampler.Color",
          "grey": True,
          "min": [0.25, 0.25, 0.25, 1],
          "max": [1, 1, 1, 1]
        }
      }
    }
```
```yaml
    {
      "module": "manipulators.MaterialManipulator",
      "config": {
        "selector": {
          "provider": "getter.Material",
          "conditions": [
          {
            "name": "bop_tless_vertex_col_material.*"
          }
          {
            "name": "bop_lm_vertex_col_material.*"
          },
          {
            "name": "bop_<args:1>_vertex_col_material.*"
          }
          ]
        },
        "cf_set_specular": {
          "provider": "sampler.Value",
          "type": "float",
          "min": 0.0,
          "max": 1.0
        },
        "cf_set_roughness": {
          "provider": "sampler.Value",
          "type": "float",
          "min": 0.0,
          "max": 1.0
        }
      }
    }
```

* Sample grey colors for T-LESS object's materials using `sampler.Color` Provider.
* Sample `specular` and `roughness` values for object's materials from all datasets using `sampler.Value` Provider.

### Basic Mesh Initializer

```yaml
    {
      "module": "constructor.BasicMeshInitializer",
      "config": {
        "meshes_to_add": [
        {
          "type": "plane",
          "name": "ground_plane0",
          "scale": [2, 2, 1]
        },
        {
          "type": "plane",
          "name": "ground_plane1",
          "scale": [2, 2, 1],
          "location": [0, -2, 2],
          "rotation": [-1.570796, 0, 0] # switch the sign to turn the normals to the outside
        },
        {
          "type": "plane",
          "name": "ground_plane2",
          "scale": [2, 2, 1],
          "location": [0, 2, 2],
          "rotation": [1.570796, 0, 0]
        },
        {
          "type": "plane",
          "name": "ground_plane4",
          "scale": [2, 2, 1],
          "location": [2, 0, 2],
          "rotation": [0, -1.570796, 0]
        },
        {
          "type": "plane",
          "name": "ground_plane5",
          "scale": [2, 2, 1],
          "location": [-2, 0, 2],
          "rotation": [0, 1.570796, 0]
        },
        {
          "type": "plane",
          "name": "light_plane",
          "location": [0, 0, 10],
          "scale": [3, 3, 1]
        }
        ]
      }
    }
```
```yaml
    {
      "module": "manipulators.EntityManipulator",
      "config": {
        "selector": {
          "provider": "getter.Entity",
          "conditions": {
            "name": '.*plane.*'
          }
        },
        "cp_physics": False,
        "cp_category_id": 333
      }
    }
```

* Construct minimal 2m x 2m x 2m room from 6 planes
* Set `"cp_physics": False` to fix the planes during any simulations

### Material Manipulator

```yaml

    {
      "module": "manipulators.MaterialManipulator",
      "config": {
        "selector": {
          "provider": "getter.Material",
          "conditions": {
            "name": "light_plane_material"
          }
        },
        "cf_switch_to_emission_shader": {
          "color": {
            "provider": "sampler.Color",
            "min": [0.5, 0.5, 0.5, 1.0],
            "max": [1.0, 1.0, 1.0, 1.0]
          },
          "strength": {
            "provider": "sampler.Value",
            "type": "float",
            "min": 3,
            "max": 6
          }
        }
      }
    }
```

* For a default material of a light plane which was created during object's initialization, switch to a Emission shader and sample `color` and `strength` values of the emitted light.

### CCMaterial Loader 

```yaml
    {
      "module": "loader.CCMaterialLoader",
      "config": {
        "folder_path": "<args:3>"
      }
    }
```

* Load a random CC0Texture that was downloaded from https://cc0textures.com/

### Entity Manipulator
```yaml
    {
      "module": "manipulators.EntityManipulator",
      "config": {
        "selector": {
          "provider": "getter.Entity",
          "conditions": {
            "name": "ground_plane.*"
          }
        },
        "mode": "once_for_all",
        "cf_randomize_materials": {
          "randomization_level": 1,
          "materials_to_replace_with": {
            "provider": "getter.Material",
            "random_samples": 1,
            "conditions": {
              "cp_is_cc_texture": True
            }
          }
        }
      }
    }
```

* Sample a CCTextures material once for all loaded ground_planes.

### On Surface Sampler

```yaml
    {
      "module": "object.OnSurfaceSampler",
      "config": {
        "objects_to_sample": {
          "provider": "getter.Entity",
          "conditions": {
            "cp_physics": True
          }
        },
        "surface": {
          "provider": "getter.Entity",
          "index": 0,
          "conditions": {
            "name": "ground_plane0"
          }
        },
        "pos_sampler": {
          "provider": "sampler.UpperRegionSampler",
          "to_sample_on": {
            "provider": "getter.Entity",
            "index": 0,
            "conditions": {
              "name": "ground_plane0"
            }
          },
          "min_height": 1,
          "max_height": 4,
          "face_sample_range": [0.4, 0.6],
          "use_ray_trace_check": False,
        },
        "min_distance": 0.01,
        "max_distance": 0.20,
        "rot_sampler": {
          "provider": "sampler.Uniform3d",
          "min": [0, 0, 0],
          "max": [0, 0, 6.28]
        }
      }
    }
```

* Get all objects with `"cp_physics": True` and the ground plane `"name": "ground_plane0"`. Use the provider `"sampler.UpperRegionSampler"` to sample objects above the plane at specified height (`"min_height", "max_height"`), relative position on plane (`"face_sample_range"`) and rotation (`"rot_sampler"`). Here, the x and y min and max rotation values are set to 0, meaning that the sampled object will stand upright at random z axis rotation. `"object.OnSurfaceSampler"` then places the objects down to the plane. Check the [on_surface_object_sampling](../on_surface_object_sampling/README.md) example for more details. 

### Light Sampler

```yaml
    {
      "module": "lighting.LightSampler",
      "config": {
        "lights": [
        {
          "location": {
            "provider": "sampler.Shell",
            "center": [0, 0, 0],
            "radius_min": 1,
            "radius_max": 1.5,
            "elevation_min": 5,
            "elevation_max": 89,
            "uniform_elevation": True
          },
          "color": {
            "provider": "sampler.Color",
            "min": [0.5, 0.5, 0.5, 1.0],
            "max": [1.0, 1.0, 1.0, 1.0]
          },
          "type": "POINT",
          "energy": 200
        }
        ]
      }
    }
```

* Samples an additional point light source (next to ceiling) in a `"sampler.Shell"` around the origin with a `"sampler.Color"` provider. 

### Camera Sampler

```yaml
    {
      "module": "camera.CameraSampler",
      "config": {
        "cam_poses": [
        {
          "proximity_checks": {
            "min": 0.3
          },
          "excluded_objs_in_proximity_check":  {
            "provider": "getter.Entity",
            "conditions": {
              "name": "ground_plane.*",
              "type": "MESH"
            }
          },
          "number_of_samples": 10,
          "location": {
            "provider": "sampler.Shell",
            "center": [0, 0, 0],
            "radius_min": 0.61,
            "radius_max": 1.24,
            "elevation_min": 5,
            "elevation_max": 89,
            "uniform_elevation": True
          },
          "rotation": {
            "format": "look_at",
            "value": {
              "provider": "getter.POI",
              "selector": {
                "provider": "getter.Entity",
                "conditions": {
                  "type": "MESH",
                  "cp_bop_dataset_name": "<args:1>",
                },
                "random_samples": 10
              }
            },
            "inplane_rot": {
              "provider": "sampler.Value",
              "type": "float",
              "min": -0.7854,
              "max": 0.7854
            }
          }
        }
        ]
      }
    }
```

* Samples `"number_of_samples": 10` camera poses, where the camera location is sampled using a `sampler.Shell` Provider with `"uniform_elevation"` sampling. 
* The camera rotation is defined by `"look_at"` a point of interest (`"getter.POI"`) plus a sampled `"inplane_rot"` in the specified range.
* The `"getter.POI"` is defined by the object closest to the mean position of all objects that are returned by the `"getter.Entity"` Provider, i.e. `"random_samples": 10` objects from the target BOP dataset `"cp_bop_dataset_name": "<args:1>"`.
* Camera poses undergo `"proximity_checks"` with respect to all objects besides ground_plane (`"excluded_objs_in_proximity_check"`) to ensure that no objects are closer than `"min": 0.3` meters.

### Rgb Renderer

```yaml
    {
      "module": "renderer.RgbRenderer",
      "config": {
        "samples": 50,
        "render_distance": True,
        "image_type": "JPEG"
      }
    }
```
* Renders RGB using 50 `"samples"`, and saves them as jpg images with 0.95 quality. Also outputs distance images. 

### Bop Writer

```yaml
    {
      "module": "writer.BopWriter",
      "config": {
        "dataset": "<args:1>",
        "append_to_existing_output": True,
        "postprocessing_modules": {
          "distance": [
            {"module": "postprocessing.Dist2Depth"}
          ]
        }
      }
    }
```

* Saves all pose and camera information that is provided in BOP datasets.
* Only considers objects from the given `"dataset": "<args:1>"`
* `"append_to_existing_output"` means that if the same output folder is chosen, data will be accumulated and not overwritten
* We use a `postprocessing.Dist2Depth` to convert the distance images from Blender to actual depth images.

## More examples

* [bop_object_pose_sampling](../bop_object_pose_sampling/README.md): Sample BOP object and camera poses.
* [bop_object_physics_positioning](../bop_object_physics_positioning/README.md): Drop BOP objects on planes and randomize materials
* [bop_scene_replication](../bop_scene_replication/README.md): Replicate the scenes and cameras from BOP datasets in simulation.
