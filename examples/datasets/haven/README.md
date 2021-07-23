# Haven 
<p align="center">
<img src="rendered_example.jpg" alt="normals and color rendering of example table" width=300>
</p>

The focus of this example is the [haven dataset](https://3dmodelhaven.com/) collection.

In order to use this example first download all the haven assets via the haven download script:

```shell
python scripts/download_haven.py
```

This will download all 3D models, all environment HDRs and also all textures they provide.

## Usage

Execute in the BlenderProc main directory:

```
python run.py examples/datasets/haven/config.yaml resources/haven/models/ArmChair_01/ArmChair_01_2k.blend resources/haven examples/datasets/haven/output
``` 

* `examples/datasets/haven/config.yaml`: path to the configuration file with pipeline configuration.
* `resources/haven/models/ArmChair_01/ArmChair_01.blend`:  Path to the blend file, from the haven dataset, browse the model folder, for all possible options
* `resources/haven`: The folder where the `hdri` folder can be found, to load an world environment
* `examples/datasets/haven/output`: path to the output directory.

## Visualization

In the output folder you will find a series of `.hdf5` containers. These can be visualized with the script:

```
python scripts/visHdf5Files.py examples/datasets/haven/output/*.hdf5
``` 

## Steps

* The BlendLoader loads the given blend file and extracts the object
* Then the `HavenEnvironmentLoader` loads a randomly selected HDR image as world environment
 
## Config file

### BlendLoader 

```yaml
{
  "module": "loader.BlendLoader",
  "config": {
    "path": "<args:0>"
  }
}
```

The `BlendLoader` loads the given blend file and extracts the object from it.

### HavenEnvironmentLoader 

```yaml
{
  "module": "loader.HavenEnvironmentLoader",
  "config": {
    "data_path": "<args:1>"
  }
}
```

This loader will load a random HDR image and will use it as an environment background for the scene.
