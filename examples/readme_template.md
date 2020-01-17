# Name of the example

![](https://i.imgur.com/KQjwKSg.png)

One-two sentences explaining the main focus of the example, e.g. focus = new module/feature we are introducing.

## Usage

Execute in the Blender-Pipeline main directory:

```
python run.py ...
``` 

Explanation of the arguments (since they are sometimes lengthy and their number may vary from example to example): 
* `examples/basic/config.yaml`: explanation
* `examples/basic/camera_positions`: explanation
* ...

## Steps

* Some step: list module(s) that are doing this step
* Some other step: `loader.ObjectLoader`
* ...

## Config file

Description of `examples/xxx/config.yaml` of version yyy.

### Some module

```yaml
    "the config": "part relevant"
    "for the module": "you are explaining"
```

`a/path/to/module` - useful if the user cant really read the config file yet.

Short description of what it is doing and what it can do.
* `"the config": "part relevant"`: Explain each line in one-two short sentences (if you documented your code well, than you can almost copy-paste the explanation + expand it here a little bit).

For each bullet point you can give a config line variation with some different `"key": "or value"` for a better understanding and shortly explain it.
* `"for the module": "you are explaining"`: ...

If some config lines are naturally gruoped and/or can be effectivelly explained in bulk like this:
* `"xxx/a": "a value"`, `"xxx/a": "a value"`, `"xxx/a": "a value"`: Then do it.

*If possible always use `"output_is_temp": False` with RGB renderer so user can just see what he got and compare it to the result image at the start of the README.*

If inside of the relevant part of the config file a sampler or a setter is used - clearly state it, explain what exactly is sampled and give `a/path/to/a/sampler/or/a/getter` and always state that any other sampler can be used here.
=> Always end the description of the config section with short description of the output if there's any. 

### Some other module

...

Finish with some recommendation about other examples that can help expand on this config file and complement this example:
* one: more on rendering
* or two examples: more on samplers