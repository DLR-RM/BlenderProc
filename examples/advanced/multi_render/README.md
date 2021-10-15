# Multiple render calls

<p align="center">
<img src="../../../images/multi_render.jpg" alt="Front readme image" width=800>
</p>

In this example we demonstrate how to render multiple times in one session.

## Usage

Execute this in the BlenderProc main directory:

```
blenderproc run examples/advanced/multi_render/main.py <PATH_TO_ShapeNetCore.v2> blenderproc_resources/vhacd examples/advanced/multi_render/output --runs 10
```

* `examples/advanced/multi_render/main.py`: path to the python file.
* `<PATH_TO_ShapeNetCore.v2>`: path to the downloaded shape net core v2 dataset, get it [here](http://www.shapenet.org/)
* `blenderproc_resources/vhacd`: The directory in which vhacd should be installed or is already installed.
* `examples/advanced/multi_render/output`: path to the output directory.
* `--run 10`: The number of times the objects should be repositioned and rendered using 2 to 5 random camera poses.

## Visualization

Visualize the generated data:

```
blenderproc vis hdf5 examples/advanced/multi_render/output/0.hdf5
```

## Steps

### Doing multiple runs

```python
# Do multiple times: Position the shapenet objects using the physics simulator and render between 2 and 5 images with random camera poses
for r in range(args.runs):
    # Clear all key frames from the previous run
    bproc.utility.reset_keyframes()

    # ... object pose sampling and rendering

    # write the data to a .hdf5 container in the run-specific output directory
    bproc.writer.write_hdf5(os.path.join(args.output_dir, str(r)), data)
```

If you want to render multiple times in one script, the only thing you need to remember is to remove all key frames before e.q. setting new camera poses.
Things like importing the objects, setting rigid body elements or creating the light should be done only once (-> outside of the for-loop).

In the end of each run, we write the new renderings into a new subdirectory of the given output directory.
You can also write everything into the same output directory, but then you would need to set `append_to_existing_output=True` when calling ` bproc.writer.write_hdf5` .