# Name of the example

Place a sample rendering here.

One-two sentences explaining the main focus of the example, e.g. new module/feature we are introducing.

## Usage

Execute in the Blender-Pipeline main directory:

```
blenderproc run ...
``` 

* `examples/advanced/YOUR_MODULE/config.yaml`: explanation
* `examples/resources/camera_positions`: explanation
* ...

## Visualization

Visualize the generated data if it is stored in a container.

```
blenderproc vis hdf5 path/to/output/0.hdf5
```

## Steps

* Some step: list module(s) that are doing this step.
* Some other step: `loader.ObjectLoader` module.
* Some other step: can be the same module(s) as in the prev point.

## Config file

### Some module

```yaml
    "the config": "section relevant"
    "for the module": "you are explaining"
```

Short description of what is going on here.

Always end the description of the config section with short description of the output if there's any. 

### Some other module

...
