# Name of the example

Place a sample rendering here.

One-two sentences explaining the main focus of the example, e.g. new module/feature we are introducing.

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py ...
``` 

* `examples/basic/config.yaml`: explanation
* `examples/basic/camera_positions`: explanation
* ...

## Visualization

Visualize the generated data if it is stored in a container.

```
python scripts/visHdf5Files.py path/to/output/0.hdf5
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


## More examples

Optionally, finish with some recommendation about other examples that can help expand on this config file and complement this example:
* one: more on rendering
* or two examples: more on samplers
