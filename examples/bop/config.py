def build_config():
    """ User-defined config file that contains a list of modules that are sequentially executed.
    
    - loads and samples the poses of BOP objects from the HomeBrew dataset
    - samples camera poses in a shell with orientation towards objects
    - uniformly samples point lights in a shell
    :returns: config that defines the procedural pipeline (dict)
    """

    total_images = 20 
    noof_cams_per_scene = 5

    pipeline_config = {
        "setup": {
          "blender_install_path": "/home_local/sund_ma/src/foreign_packages",
          "blender_version": "blender-2.80-linux-glibc217-x86_64",
          "pip": [ "h5py", "imageio", "pypng==0.0.18", "scipy==1.2.2" ]
        },
        "global": {
            "all": {
                "output_dir": "<args:1>",
                "sys_paths": ["/home_local/sund_ma/src/foreign_packages/bop/bop_toolkit-1"]
            }
        }
    }

    modules = []

    modules.append("main.Initializer")
    modules.append({
      "name": "loader.BopLoader",
      "config": {
        "bop_dataset_path": "<args:0>",
        "mm2m": True,
        "split": "val",
        "obj_ids": [1,1,3],
        "model_type": ""
      }
    })
    modules.append({
         "name": "lighting.LightSampler",
         "config": {
           "lights": [
             {
               "location": {
                 "name": "ShellSampler",
                 "parameters": {
                   "center": [0, 0, -0.8],
                   "radius_min": 1,
                   "radius_max": 4,
                   "elevation_min": 1,
                   "elevation_max": 89
                 }
               },
               "type": "POINT",
               "energy": 1000
             }
           ]
         }
       })  

    modules.append({
      "name": "composite.CameraObjectSampler",
      "config": {
        "total_noof_cams": 10,
        "noof_cams_per_scene": 5,
        "object_pose_sampler": {
          "name": "object.ObjectPoseSampler",
          "config": {
            "max_iterations": 1000,
            "pos_sampler": {
              "name": "Uniform3dSampler",
              "parameters": {
                  "max": [0.5, 0.5, 0.5],
                  "min": [-0.5, -0.5, -0.5]
              }
            },
            "rot_sampler": {
              "name": "Uniform3dSampler",
              "parameters": {
                  "max": [0, 0, 0],
                  "min": [6.28, 6.28, 6.28]
              }
            }
          }
        },
        "camera_pose_sampler": {
          "name": "camera.CameraSampler",
          "config": {
            "cam_poses": [
              {
                "location": {
                  "name": "ShellSampler",
                  "parameters": {
                    "center": [0, 0, 0],
                    "radius_min": 0.8,
                    "radius_max": 1.2,
                    "elevation_min": 1,
                    "elevation_max": 89
                  }
                },
                "rotation": {
                  "format": "look_at",
                  "value": {
                    "name": "POIGetter",
                    "parameters": {}
                  }
                }
              }
            ]
          }
        }
      }
    })
    
    modules.append({
      "name": "renderer.RgbRenderer",
      "config": {
        "samples": 150
      }
    })
    modules.append({
      "name": "renderer.SegMapRenderer",
      "config": {
        "map_by": "instance"
      }
    })
    modules.append({
      "name": "writer.CocoAnnotationsWriter",
      "config": {
      }
    })
    modules.append({
      "name": "writer.Hdf5Writer",
      "config": {
      }
    })

    pipeline_config["modules"] = modules

    return pipeline_config
